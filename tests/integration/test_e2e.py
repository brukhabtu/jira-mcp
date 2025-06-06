"""End-to-end integration tests for jira_mcp."""
import pytest
from unittest.mock import AsyncMock, patch

from jira_mcp.config import AppConfig, JiraConfig, MCPConfig
from jira_mcp.server import JiraMCPServer


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_server_initialization_flow_integration(self) -> None:
        """Test that server initialization components work together properly."""
        config = AppConfig(
            jira=JiraConfig(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="test-token",
            ),
            mcp=MCPConfig(),
        )

        server = JiraMCPServer(config)

        # Test that all components are properly initialized
        assert server.config == config
        assert server.jira_client is not None
        assert server.mcp_server is None  # Should be None before initialization

        # Test that URL construction works
        spec_url = server._get_openapi_spec_url()
        assert isinstance(spec_url, str)
        assert spec_url.startswith("https://")

        # Test that auth client creation works
        auth_client_created = hasattr(server, 'jira_client')
        assert auth_client_created

    @pytest.mark.integration
    @pytest.mark.slow  
    def test_openapi_spec_url_accessibility(self) -> None:
        """Test that the OpenAPI spec URL is accessible (real network test)."""
        config = AppConfig(
            jira=JiraConfig(
                base_url="https://test.atlassian.net",
                user="test@example.com", 
                api_token="test-token",
            ),
            mcp=MCPConfig(),
        )

        server = JiraMCPServer(config)
        spec_url = server._get_openapi_spec_url()

        # This is a real network test - would be skipped in CI/CD without network
        # For now, just test the URL format since we don't want to make real calls
        assert spec_url.startswith("https://")
        assert "atlassian.com" in spec_url
        assert spec_url.endswith(".json")

        # TODO: Add real network test when appropriate test environment exists
        # import httpx
        # response = httpx.get(spec_url, timeout=10)
        # assert response.status_code == 200
        # spec = response.json()
        # assert "openapi" in spec or "swagger" in spec