"""Integration tests for server functionality."""

from unittest.mock import Mock

import pytest

from jira_mcp.settings import AppSettings, JiraSettings, MCPSettings
from jira_mcp.server import JiraMCPServer


class TestServerIntegration:
    """Integration tests for JiraMCPServer."""

    @pytest.mark.integration
    def test_server_run_requires_initialization(self) -> None:
        """Test that run() fails if server not initialized (integration test)."""
        settings = AppSettings(
            jira=JiraSettings(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="token",
            ),
            mcp=MCPSettings(),
        )

        server = JiraMCPServer(settings)

        # Should raise error when trying to run uninitialized server
        with pytest.raises(RuntimeError, match="Server not initialized"):
            server.run()

    @pytest.mark.integration
    def test_server_unsupported_transport_raises_error(self) -> None:
        """Test that unsupported transport configurations raise appropriate errors."""
        settings = AppSettings(
            jira=JiraSettings(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="token",
            ),
            mcp=MCPSettings(transport="invalid-transport"),
        )

        server = JiraMCPServer(settings)

        # Mock an initialized server with invalid transport
        server.mcp_server = Mock()

        with pytest.raises(
            ValueError, match="Unsupported transport: invalid-transport"
        ):
            server.run()
