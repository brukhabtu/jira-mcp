"""Integration tests for server functionality."""

from unittest.mock import Mock

import pytest

from jira_mcp.config import AppConfig, JiraConfig, MCPConfig
from jira_mcp.server import JiraMCPServer


class TestServerIntegration:
    """Integration tests for JiraMCPServer."""

    @pytest.mark.integration
    def test_server_run_requires_initialization(self) -> None:
        """Test that run() fails if server not initialized (integration test)."""
        config = AppConfig(
            jira=JiraConfig(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="token",
            ),
            mcp=MCPConfig(),
        )

        server = JiraMCPServer(config)

        # Should raise error when trying to run uninitialized server
        with pytest.raises(RuntimeError, match="Server not initialized"):
            server.run()

    @pytest.mark.integration
    def test_server_unsupported_transport_raises_error(self) -> None:
        """Test that unsupported transport configurations raise appropriate errors."""
        config = AppConfig(
            jira=JiraConfig(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="token",
            ),
            mcp=MCPConfig(transport="invalid-transport"),
        )

        server = JiraMCPServer(config)

        # Mock an initialized server with invalid transport
        server.mcp_server = Mock()

        with pytest.raises(
            ValueError, match="Unsupported transport: invalid-transport"
        ):
            server.run()
