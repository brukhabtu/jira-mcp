"""End-to-end integration tests for jira_mcp."""

import pytest

from jira_mcp.settings import AppSettings, JiraSettings, MCPSettings
from jira_mcp.server import JiraMCPServer


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_server_initialization_flow_integration(self) -> None:
        """Test that server initialization components work together properly."""
        settings = AppSettings(
            jira=JiraSettings(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="test-token",
            ),
            mcp=MCPSettings(),
        )

        server = JiraMCPServer(settings)

        # Test that all components are properly initialized
        assert server.config == settings
        assert server.jira_client is not None
        assert server.mcp_server is None  # Should be None before initialization

        # Test that bundled spec path works
        spec_path = server._get_bundled_spec_path()
        assert spec_path.exists()
        assert spec_path.name == "jira_openapi_spec.json"

        # Test that auth client creation works
        auth_client_created = hasattr(server, "jira_client")
        assert auth_client_created

    @pytest.mark.integration
    @pytest.mark.slow
    def test_bundled_spec_loading(self) -> None:
        """Test that the bundled OpenAPI spec loads correctly."""
        settings = AppSettings(
            jira=JiraSettings(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="test-token",
            ),
            mcp=MCPSettings(),
        )

        server = JiraMCPServer(settings)

        # Test that the bundled spec loads without errors
        spec = server._load_openapi_spec()

        # Verify it's a valid OpenAPI spec
        assert isinstance(spec, dict)
        assert "openapi" in spec
        assert "paths" in spec
        assert "info" in spec

        # Should have a reasonable number of endpoints
        assert len(spec["paths"]) > 100  # Jira has many endpoints
        # assert "openapi" in spec or "swagger" in spec
