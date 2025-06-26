"""Jira MCP server using FastMCP OpenAPI integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

# Import patches to apply them
from . import patches  # noqa: F401

if TYPE_CHECKING:
    from fastmcp.server.openapi import FastMCPOpenAPI

from jira_mcp.auth import JiraClient
from jira_mcp.settings import AppSettings


class JiraMCPServer:
    """MCP server for Jira integration using FastMCP OpenAPI."""

    def __init__(self, config: AppSettings) -> None:
        """Initialize the server with configuration."""
        self.config = config
        self.jira_client = JiraClient(config.jira)
        self.mcp_server: FastMCPOpenAPI | None = None

    def _get_bundled_spec_path(self) -> Path:
        """Get the path to the bundled OpenAPI specification."""
        return Path(__file__).parent / "jira_openapi_spec.json"

    def _load_openapi_spec(self) -> dict[str, Any]:
        """Load the OpenAPI specification from file or use bundled version."""
        import logging

        logger = logging.getLogger("jira_mcp")

        # Use custom path if provided, otherwise use bundled spec
        if self.config.jira.openapi_spec_path:
            spec_path = Path(self.config.jira.openapi_spec_path)
            logger.info(f"Using custom OpenAPI spec: {spec_path}")
        else:
            spec_path = self._get_bundled_spec_path()
            logger.info("Using bundled OpenAPI spec")

        try:
            with open(spec_path, encoding="utf-8") as f:
                spec: dict[str, Any] = json.load(f)
                return spec
        except FileNotFoundError as e:
            msg = f"OpenAPI spec file not found: {spec_path}"
            raise FileNotFoundError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in OpenAPI spec file {spec_path}: {e}"
            raise ValueError(msg) from e

    async def _create_authenticated_client(self) -> httpx.AsyncClient:
        """Create an authenticated HTTP client for Jira API calls."""
        auth_header = self.jira_client.get_auth_headers()["Authorization"]
        basic_token = auth_header.split(" ")[1]
        headers = {
            "Authorization": f"Basic {basic_token}",
            "Content-Type": "application/json",
        }

        return httpx.AsyncClient(
            base_url=self.config.jira.base_url,
            headers=headers,
            timeout=self.config.jira.timeout,
        )


    def _load_route_config(self) -> list[str]:
        """Load route configuration from YAML file if specified."""
        if not self.config.mcp.route_config_path:
            return []
            
        import logging
        logger = logging.getLogger("jira_mcp")
        
        try:
            config_path = Path(self.config.mcp.route_config_path)
            with open(config_path, encoding="utf-8") as f:
                try:
                    import yaml
                    config_data = yaml.safe_load(f)
                except ImportError as e:
                    msg = f"YAML support requires PyYAML: pip install PyYAML"
                    raise ImportError(msg) from e
            
            # Handle named configurations
            if self.config.mcp.route_config_name:
                config_name = self.config.mcp.route_config_name
                if "configurations" in config_data:
                    if config_name in config_data["configurations"]:
                        routes = config_data["configurations"][config_name].get("routes", [])
                        logger.info(f"Loaded {len(routes)} routes from configuration '{config_name}' in {config_path}")
                        return routes
                    else:
                        available = list(config_data["configurations"].keys())
                        logger.error(f"Configuration '{config_name}' not found. Available: {available}")
                        return []
                else:
                    logger.error(f"No 'configurations' section found in {config_path}")
                    return []
            else:
                # Fallback to direct routes array for backward compatibility
                routes = config_data.get("routes", [])
                logger.info(f"Loaded {len(routes)} routes from {config_path}")
                return routes
            
        except Exception as e:
            logger.error(f"Failed to load route config from {self.config.mcp.route_config_path}: {e}")
            return []

    def _get_safe_endpoints(self) -> list[str]:
        """Get the list of safe endpoints from configuration file."""
        import logging
        logger = logging.getLogger("jira_mcp")
        
        # Route configuration is required
        if not self.config.mcp.route_config_path or not self.config.mcp.route_config_name:
            msg = "Route configuration is required. Set MCP_ROUTE_CONFIG_PATH and MCP_ROUTE_CONFIG_NAME environment variables."
            raise ValueError(msg)
        
        # Load routes from file
        file_routes = self._load_route_config()
        if not file_routes:
            msg = f"Failed to load configuration '{self.config.mcp.route_config_name}' from {self.config.mcp.route_config_path}"
            raise ValueError(msg)
        
        logger.info(f"Using configuration '{self.config.mcp.route_config_name}' with {len(file_routes)} routes")
        return file_routes

    def _get_route_filters(self) -> list[RouteMap] | None:
        """Get route filtering rules based on configuration.

        Security Model:
        1. Load endpoints from YAML configuration
        2. Check if configuration includes destructive operations
        3. Apply appropriate filtering

        Returns None if configuration explicitly allows all operations.
        """
        safe_endpoints = self._get_safe_endpoints()
        
        # Check if configuration includes the "all operations" pattern
        # If so, disable filtering entirely (like the old "unsafe" preset)
        if any(pattern in [r"^/rest/api/.*", "^/rest/api/.*"] for pattern in safe_endpoints):
            import logging
            logger = logging.getLogger("jira_mcp")
            logger.warning("Configuration includes all API endpoints - NO FILTERING applied! Destructive operations are possible.")
            return None

        filters = [
            # SECURITY: Block ALL destructive operations first
            RouteMap(
                methods=["POST", "PUT", "PATCH", "DELETE"], mcp_type=MCPType.EXCLUDE
            ),
        ]

        # Add configured endpoints (GET only by default)
        filters.extend(
            RouteMap(
                pattern=pattern,
                methods=["GET"],
                mcp_type=MCPType.TOOL,
            )
            for pattern in safe_endpoints
        )

        # SECURITY: Default deny everything else
        filters.append(RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE))

        return filters

    async def initialize(self) -> None:
        """Initialize the FastMCP server with Jira OpenAPI spec."""
        import logging

        logger = logging.getLogger("jira_mcp")

        # Load OpenAPI specification
        openapi_spec = self._load_openapi_spec()

        # Create authenticated client
        auth_client = await self._create_authenticated_client()

        # Create FastMCP server from OpenAPI specification with route filtering
        route_maps = self._get_route_filters()
        if route_maps is None:
            logger.warning("No route filtering - ALL endpoints exposed!")
        else:
            logger.info("Safe route filtering enabled - only read-only endpoints exposed")

        self.mcp_server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=auth_client,
            route_maps=route_maps,
        )

    def run(self) -> None:
        """Run the MCP server with the configured transport."""
        if not self.mcp_server:
            msg = "Server not initialized. Call initialize() first."
            raise RuntimeError(msg)

        transport = self.config.mcp.transport

        if transport == "stdio":
            self.mcp_server.run("stdio")
        elif transport == "http":
            self.mcp_server.run("streamable-http", port=self.config.mcp.port)
        elif transport == "sse":
            self.mcp_server.run("sse", port=self.config.mcp.port)
        else:
            msg = f"Unsupported transport: {transport}"
            raise ValueError(msg)

    async def start(self) -> None:
        """Initialize and run the server."""
        await self.initialize()
        # Note: run() is synchronous and will block
        self.run()
