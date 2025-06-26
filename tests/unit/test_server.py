"""Unit tests for MCP server functionality."""

import pytest
from fastmcp.server.openapi import MCPType

from jira_mcp.settings import AppSettings, JiraSettings, MCPSettings
from jira_mcp.server import JiraMCPServer


class TestJiraMCPServer:
    """Tests for JiraMCPServer initialization and configuration."""

    def test_server_initialization_stores_config(
        self, sample_app_settings: AppSettings
    ) -> None:
        """Test that server properly stores and initializes with configuration."""
        server = JiraMCPServer(sample_app_settings)

        # Verify config storage
        assert server.config == sample_app_settings
        assert server.config.jira.base_url == "https://test.atlassian.net"
        assert server.config.mcp.transport == "stdio"

        # Verify jira client was created
        assert server.jira_client is not None
        assert server.jira_client.base_url == "https://test.atlassian.net"
        assert server.jira_client.user == "test@example.com"

    def test_server_starts_uninitialized(self, sample_app_settings: AppSettings) -> None:
        """Test that server starts in uninitialized state."""
        server = JiraMCPServer(sample_app_settings)

        # Should start with no MCP server instance
        assert server.mcp_server is None

    def test_bundled_spec_path_exists(self, sample_app_settings: AppSettings) -> None:
        """Test that bundled OpenAPI spec path is correct."""
        server = JiraMCPServer(sample_app_settings)
        spec_path = server._get_bundled_spec_path()

        # Should be a Path object pointing to the bundled spec
        assert spec_path.name == "jira_openapi_spec.json"
        assert spec_path.parent.name == "jira_mcp"

        # The file should exist (since we bundled it)
        assert spec_path.exists(), f"Bundled spec file not found: {spec_path}"

    @pytest.mark.parametrize(
        "transport,port",
        [
            ("stdio", 8000),
            ("http", 8080),
            ("sse", 9000),
        ],
    )
    def test_transport_validation_logic(
        self, sample_jira_settings: JiraSettings, transport: str, port: int
    ) -> None:
        """Test the transport selection logic without external dependencies."""
        settings = AppSettings(
            jira=sample_jira_settings,
            mcp=MCPSettings(transport=transport, port=port),
        )

        server = JiraMCPServer(settings)

        assert server.config.mcp.transport == transport
        assert server.config.mcp.port == port

    def test_load_openapi_spec_bundled(self, sample_app_settings: AppSettings) -> None:
        """Test that _load_openapi_spec method loads the bundled spec correctly."""
        server = JiraMCPServer(sample_app_settings)

        # Test loading the bundled spec
        spec = server._load_openapi_spec()
        assert isinstance(spec, dict)
        assert "openapi" in spec
        assert "paths" in spec
        assert len(spec["paths"]) > 0

    def test_load_openapi_spec_custom_path(
        self, sample_jira_settings: JiraSettings
    ) -> None:
        """Test that custom OpenAPI spec path is used when provided."""
        # Create config with custom spec path
        custom_jira_settings = JiraSettings(
            base_url=sample_jira_settings.base_url,
            user=sample_jira_settings.user,
            api_token=sample_jira_settings.api_token,
            timeout=sample_jira_settings.timeout,
            openapi_spec_path="/custom/path/spec.json",
        )
        settings = AppSettings(jira=custom_jira_settings, mcp=MCPSettings())
        server = JiraMCPServer(settings)

        # Should use custom path (even if file doesn't exist, path should be used)
        import pytest

        with pytest.raises(FileNotFoundError, match="/custom/path/spec.json"):
            server._load_openapi_spec()

    def test_jira_client_configuration_propagation(self) -> None:
        """Test that Jira client gets correct configuration from server config."""
        jira_settings = JiraSettings(
            base_url="https://custom.atlassian.net",
            user="custom@example.com",
            api_token="custom-token-456",
            timeout=60,
        )

        app_settings = AppSettings(jira=jira_settings, mcp=MCPSettings())

        server = JiraMCPServer(app_settings)

        # Verify that the JiraClient received the correct config
        assert server.jira_client.base_url == "https://custom.atlassian.net"
        assert server.jira_client.user == "custom@example.com"
        assert server.jira_client.api_token == "custom-token-456"
        assert server.jira_client.timeout == 60

    def test_route_filters_exclude_destructive_operations(
        self, sample_app_settings: AppSettings
    ) -> None:
        """Test that route filters properly exclude destructive HTTP methods."""
        server = JiraMCPServer(sample_app_settings)
        route_filters = server._get_route_filters()

        # Find the destructive methods filter
        destructive_filter = next(
            f
            for f in route_filters
            if f.methods and set(f.methods) == {"POST", "PUT", "PATCH", "DELETE"}
        )
        assert destructive_filter.mcp_type == MCPType.EXCLUDE

    def test_route_filters_include_safe_endpoints(
        self, sample_app_settings: AppSettings
    ) -> None:
        """Test that route filters include safe read-only endpoints."""
        server = JiraMCPServer(sample_app_settings)
        route_filters = server._get_route_filters()

        # Check for issue search endpoint
        search_filter = next(
            f for f in route_filters if f.pattern and "search" in f.pattern
        )
        assert search_filter.mcp_type == MCPType.TOOL
        assert search_filter.methods == ["GET"]

    def test_route_filters_have_default_exclude(
        self, sample_app_settings: AppSettings
    ) -> None:
        """Test that route filters have a catch-all exclude rule."""
        server = JiraMCPServer(sample_app_settings)
        route_filters = server._get_route_filters()

        # Last filter should be catch-all exclude
        default_filter = route_filters[-1]
        assert default_filter.pattern == r".*"
        assert default_filter.mcp_type == MCPType.EXCLUDE

    @pytest.mark.parametrize(
        "endpoint_pattern,expected_included",
        [
            (r"^/rest/api/3/issue/[^/]+$", True),  # Issue details
            (r"^/rest/api/3/search$", True),  # Issue search
            (r"^/rest/api/3/project.*", True),  # Project info
            (r"^/rest/api/3/board.*", True),  # Board info
            (r"^/rest/api/3/admin.*", False),  # Admin endpoints
            (r"^/rest/api/3/issue/.*/delete", False),  # Delete operations
        ],
    )
    def test_endpoint_pattern_filtering(
        self,
        sample_app_settings: AppSettings,
        endpoint_pattern: str,
        expected_included: bool,
    ) -> None:
        """Test that specific endpoint patterns are correctly included or excluded."""
        server = JiraMCPServer(sample_app_settings)
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
            assert not pattern_exists, (
                f"Expected pattern {endpoint_pattern} to be excluded"
            )
