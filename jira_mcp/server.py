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
from jira_mcp.config import AppConfig


class JiraMCPServer:
    """MCP server for Jira integration using FastMCP OpenAPI."""

    def __init__(self, config: AppConfig) -> None:
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

    def _get_route_filters(self) -> list[RouteMap]:
        """Get route filtering rules for safe engineering-focused tools.

        Security Model:
        1. DENY ALL destructive operations (POST, PUT, PATCH, DELETE)
        2. ALLOW ONLY specific read-only GET endpoints
        3. DEFAULT DENY everything else

        This whitelist approach ensures only safe, read-only operations
        are exposed through the MCP interface.
        """
        # Define safe read-only endpoints for engineering workflows
        safe_endpoints = [
            # Core issue management (read-only)
            r"^/rest/api/3/issue/[^/]+$",  # Get single issue
            r"^/rest/api/3/search$",  # Search issues/JQL
            r"^/rest/api/3/issue/[^/]+/comment.*",  # Issue comments
            r"^/rest/api/3/issue/[^/]+/changelog.*",  # Issue history
            r"^/rest/api/3/issue/[^/]+/worklog.*",  # Time tracking
            # Project and structure information
            r"^/rest/api/3/project.*",  # Project details
            r"^/rest/api/3/issuetype.*",  # Issue types
            r"^/rest/api/3/status.*",  # Workflow statuses
            r"^/rest/api/3/priority.*",  # Issue priorities
            r"^/rest/api/3/resolution.*",  # Issue resolutions
            # Agile/Scrum information
            r"^/rest/api/3/board.*",  # Agile boards
            r"^/rest/api/3/sprint.*",  # Sprint information
            # User and team information
            r"^/rest/api/3/user.*",  # User profiles
            r"^/rest/api/3/group.*",  # User groups
            # Dashboards and reporting
            r"^/rest/api/3/dashboard.*",  # Dashboard data
            r"^/rest/api/3/filter.*",  # Saved filters
            # System information (safe metadata)
            r"^/rest/api/3/serverInfo$",  # Server version info
            r"^/rest/api/3/field.*",  # Custom fields metadata
        ]

        filters = [
            # SECURITY: Block ALL destructive operations first
            RouteMap(
                methods=["POST", "PUT", "PATCH", "DELETE"], mcp_type=MCPType.EXCLUDE
            ),
        ]

        # Add whitelisted read-only endpoints
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

        # Create FastMCP server from OpenAPI specification
        if self.config.mcp.enable_security_filtering:
            # Use security filtering (default, recommended)
            route_maps = self._get_route_filters()
            logger.info(
                "Security filtering ENABLED - only safe read-only endpoints exposed"
            )
        else:
            # WARNING: No security filtering - exposes ALL Jira API endpoints
            route_maps = None
            logger.warning(
                "Security filtering DISABLED - ALL Jira API endpoints exposed including destructive operations!"
            )

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
