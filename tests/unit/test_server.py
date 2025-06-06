"""Unit tests for MCP server functionality."""
import pytest
from fastmcp.server.openapi import MCPType, RouteMap

from jira_mcp.config import AppConfig, JiraConfig, MCPConfig
from jira_mcp.server import JiraMCPServer


class TestJiraMCPServer:
    """Tests for JiraMCPServer initialization and configuration."""

    def test_server_initialization_stores_config(self, sample_app_config: AppConfig) -> None:
        """Test that server properly stores and initializes with configuration."""
        server = JiraMCPServer(sample_app_config)

        # Verify config storage
        assert server.config == sample_app_config
        assert server.config.jira.base_url == "https://test.atlassian.net"
        assert server.config.mcp.transport == "stdio"

        # Verify jira client was created
        assert server.jira_client is not None
        assert server.jira_client.base_url == "https://test.atlassian.net"
        assert server.jira_client.user == "test@example.com"

    def test_server_starts_uninitialized(self, sample_app_config: AppConfig) -> None:
        """Test that server starts in uninitialized state."""
        server = JiraMCPServer(sample_app_config)

        # Should start with no MCP server instance
        assert server.mcp_server is None

    def test_openapi_spec_url_is_stable(self, sample_app_config: AppConfig) -> None:
        """Test that OpenAPI spec URL is the expected Jira endpoint."""
        server = JiraMCPServer(sample_app_config)
        spec_url = server._get_openapi_spec_url()

        # This URL should be stable and point to Jira's official spec
        expected_url = "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
        assert spec_url == expected_url

        # Verify it's a valid URL format
        assert spec_url.startswith("https://")
        assert "atlassian.com" in spec_url
        assert spec_url.endswith(".json")

    @pytest.mark.parametrize(
        "transport,port",
        [
            ("stdio", 8000),
            ("http", 8080),
            ("sse", 9000),
        ],
    )
    def test_transport_validation_logic(
        self, sample_jira_config: JiraConfig, transport: str, port: int
    ) -> None:
        """Test the transport selection logic without external dependencies."""
        config = AppConfig(
            jira=sample_jira_config,
            mcp=MCPConfig(transport=transport, port=port),
        )

        server = JiraMCPServer(config)

        assert server.config.mcp.transport == transport
        assert server.config.mcp.port == port

    def test_get_openapi_spec_url_method(self, sample_app_config: AppConfig) -> None:
        """Test that _get_openapi_spec_url method works correctly."""
        server = JiraMCPServer(sample_app_config)
        
        # Test the method exists and returns a string
        spec_url = server._get_openapi_spec_url()
        assert isinstance(spec_url, str)
        assert len(spec_url) > 0

    def test_jira_client_configuration_propagation(self) -> None:
        """Test that Jira client gets correct configuration from server config."""
        jira_config = JiraConfig(
            base_url="https://custom.atlassian.net",
            user="custom@example.com",
            api_token="custom-token-456",
            timeout=60,
        )

        app_config = AppConfig(jira=jira_config, mcp=MCPConfig())

        server = JiraMCPServer(app_config)

        # Verify that the JiraClient received the correct config
        assert server.jira_client.base_url == "https://custom.atlassian.net"
        assert server.jira_client.user == "custom@example.com"
        assert server.jira_client.api_token == "custom-token-456"
        assert server.jira_client.timeout == 60

    def test_route_filters_exclude_destructive_operations(self, sample_app_config: AppConfig) -> None:
        """Test that route filters properly exclude destructive HTTP methods."""
        server = JiraMCPServer(sample_app_config)
        route_filters = server._get_route_filters()

        # Find the destructive methods filter
        destructive_filter = next(
            f for f in route_filters 
            if f.methods and set(f.methods) == {"POST", "PUT", "PATCH", "DELETE"}
        )
        assert destructive_filter.mcp_type == MCPType.EXCLUDE

    def test_route_filters_include_safe_endpoints(self, sample_app_config: AppConfig) -> None:
        """Test that route filters include safe read-only endpoints."""
        server = JiraMCPServer(sample_app_config)
        route_filters = server._get_route_filters()

        # Check for issue search endpoint
        search_filter = next(
            f for f in route_filters 
            if f.pattern and "search" in f.pattern
        )
        assert search_filter.mcp_type == MCPType.TOOL
        assert search_filter.methods == ["GET"]

    def test_route_filters_have_default_exclude(self, sample_app_config: AppConfig) -> None:
        """Test that route filters have a catch-all exclude rule."""
        server = JiraMCPServer(sample_app_config)
        route_filters = server._get_route_filters()

        # Last filter should be catch-all exclude
        default_filter = route_filters[-1]
        assert default_filter.pattern == r".*"
        assert default_filter.mcp_type == MCPType.EXCLUDE

    @pytest.mark.parametrize(
        "endpoint_pattern,expected_included",
        [
            (r"^/rest/api/3/issue/[^/]+$", True),  # Issue details
            (r"^/rest/api/3/search$", True),        # Issue search
            (r"^/rest/api/3/project.*", True),      # Project info
            (r"^/rest/api/3/board.*", True),        # Board info
            (r"^/rest/api/3/admin.*", False),       # Admin endpoints
            (r"^/rest/api/3/issue/.*/delete", False),  # Delete operations
        ],
    )
    def test_endpoint_pattern_filtering(
        self, sample_app_config: AppConfig, endpoint_pattern: str, expected_included: bool
    ) -> None:
        """Test that specific endpoint patterns are correctly included or excluded."""
        server = JiraMCPServer(sample_app_config)
        route_filters = server._get_route_filters()

        # Check if pattern exists in filters
        pattern_exists = any(
            f.pattern == endpoint_pattern and f.mcp_type == MCPType.TOOL 
            for f in route_filters
        )
        
        if expected_included:
            assert pattern_exists, f"Expected pattern {endpoint_pattern} to be included"
        else:
            # Pattern shouldn't exist as a TOOL, should be excluded by default
            assert not pattern_exists, f"Expected pattern {endpoint_pattern} to be excluded"
