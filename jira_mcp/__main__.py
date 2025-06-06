"""Main entry point for the Jira MCP server."""
from __future__ import annotations

import argparse
import logging
import sys

from jira_mcp.config import AppConfig


def setup_logging(transport: str) -> logging.Logger:
    """Set up logging for the application."""
    logger = logging.getLogger("jira_mcp")
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # For stdio transport, log to stderr to avoid interfering with MCP protocol
    if transport == "stdio":
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def main() -> None:
    """Main entry point for the Jira MCP server."""
    parser = argparse.ArgumentParser(
        prog="jira-mcp",
        description="Jira MCP Server using FastMCP 2.0 OpenAPI Integration",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        help="Transport method for MCP server (overrides MCP_TRANSPORT env var)",
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port for HTTP/SSE transport (overrides MCP_PORT env var)",
    )

    args = parser.parse_args()

    # Load configuration from environment variables
    try:
        config = AppConfig.from_env()

        # Use command line overrides if provided
        if args.transport:
            config.mcp.transport = args.transport
        if args.port:
            config.mcp.port = args.port

        # Set up logging with correct transport
        logger = setup_logging(config.mcp.transport)

        logger.info("Jira MCP Server v0.1.0")
        logger.info("Jira URL: %s", config.jira.base_url)
        logger.info("Jira User: %s", config.jira.user)
        logger.info("Transport: %s", config.mcp.transport)
        if config.mcp.transport != "stdio":
            logger.info("Port: %s", config.mcp.port)

    except ValueError as e:
        # Can't set up logger yet, so fall back to stderr
        sys.stderr.write(f"Configuration error: {e}\n")
        sys.stderr.write("Required environment variables:\n")
        sys.stderr.write("  JIRA_BASE_URL - Your Jira instance URL\n")
        sys.stderr.write("  JIRA_API_USER - Your Jira username/email\n")
        sys.stderr.write("  JIRA_API_TOKEN - Your Jira API token\n")
        return

    # Initialize and run the MCP server
    logger.info("Starting Jira MCP server...")
    try:
        from jira_mcp.server import JiraMCPServer
        server = JiraMCPServer(config)

        # Initialize the server async components
        import asyncio
        asyncio.run(server.initialize())

        # Run the MCP server (this will block)
        server.run()
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Failed to start server: %s", e)
        return


if __name__ == "__main__":
    main()
