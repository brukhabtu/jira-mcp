"""Jira MCP server using FastMCP OpenAPI integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

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

    def _get_openapi_spec_url(self) -> str:
        """Get the URL for Jira's OpenAPI specification."""
        return "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"

    async def _fetch_openapi_spec(self) -> dict[str, Any]:
        """Fetch the OpenAPI specification from Jira."""
        spec_url = self._get_openapi_spec_url()

        async with httpx.AsyncClient() as client:
            response = await client.get(spec_url)
            response.raise_for_status()
            spec: dict[str, Any] = response.json()
            return spec

    async def _create_authenticated_client(self) -> httpx.AsyncClient:
        """Create an authenticated HTTP client for Jira API calls."""
        auth_header = self.jira_client.get_auth_headers()["Authorization"]
        basic_token = auth_header.split(" ")[1]
        headers = {
            "Authorization": f"Basic {basic_token}",
            "Content-Type": "application/json"
        }

        return httpx.AsyncClient(
            base_url=self.config.jira.base_url,
            headers=headers,
            timeout=self.config.jira.timeout
        )

    def _get_route_filters(self) -> list[RouteMap]:
        """Get route filtering rules for safe engineering-focused tools."""
        return [
            # Exclude all destructive operations
            RouteMap(methods=["POST", "PUT", "PATCH", "DELETE"], mcp_type=MCPType.EXCLUDE),

            # Include safe read-only endpoints for engineering teams
            RouteMap(pattern=r"^/rest/api/3/issue/[^/]+$", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/search$", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/project.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/board.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/sprint.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/user.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/issue/[^/]+/comment.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/issue/[^/]+/changelog.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/issue/[^/]+/worklog.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/dashboard.*", methods=["GET"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/rest/api/3/filter.*", methods=["GET"], mcp_type=MCPType.TOOL),

            # Exclude everything else by default
            RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE)
        ]

    async def initialize(self) -> None:
        """Initialize the FastMCP server with Jira OpenAPI spec."""
        # Fetch OpenAPI specification
        openapi_spec = await self._fetch_openapi_spec()

        # Create authenticated client
        auth_client = await self._create_authenticated_client()

        # Create FastMCP server from OpenAPI specification with filtering
        self.mcp_server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=auth_client,
            route_maps=self._get_route_filters()
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
