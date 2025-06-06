"""Integration tests for CLI functionality."""
import contextlib
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCLIIntegration:
    """Integration tests for the CLI interface."""

    @pytest.mark.integration
    def test_main_with_help_flag(self) -> None:
        """Test that main function can handle help flag without crashing."""
        from jira_mcp.__main__ import main

        with patch("sys.argv", ["jira-mcp", "--help"]):
            # Should not raise exception when called with help
            try:
                main()
            except SystemExit as e:
                # Help flag typically causes SystemExit(0)
                assert e.code == 0

    @pytest.mark.integration
    def test_main_with_env_vars(self) -> None:
        """Test main function loads configuration from environment variables."""
        from jira_mcp.__main__ import main

        # Set test environment variables
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_API_USER"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "test-token"

        try:
            with patch("sys.argv", ["jira-mcp"]), patch(
                "jira_mcp.server.JiraMCPServer"
            ) as mock_server_class:
                # Mock the server initialization to avoid network calls
                mock_server = mock_server_class.return_value
                mock_server.initialize.return_value = None
                mock_server.run.side_effect = KeyboardInterrupt()  # Simulate graceful exit

                with contextlib.suppress(KeyboardInterrupt):
                    main()

            # Verify server was created with correct config
            mock_server_class.assert_called_once()
            config = mock_server_class.call_args[0][0]
            assert config.jira.base_url == "https://test.atlassian.net"
            assert config.jira.user == "test@example.com"
            assert config.jira.api_token == "test-token"

        finally:
            del os.environ["JIRA_BASE_URL"]
            del os.environ["JIRA_API_USER"]
            del os.environ["JIRA_API_TOKEN"]

    @pytest.mark.integration
    def test_main_missing_env_vars(self) -> None:
        """Test main function handles missing environment variables gracefully."""
        from jira_mcp.__main__ import main

        # Ensure required env vars are not set
        for var in ["JIRA_BASE_URL", "JIRA_API_USER", "JIRA_API_TOKEN"]:
            if var in os.environ:
                del os.environ[var]

        with patch("sys.argv", ["jira-mcp"]), patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr:
            main()

            # Check that error message was written to stderr
            stderr_output = mock_stderr.getvalue()
            assert "Configuration error" in stderr_output
            assert "JIRA_BASE_URL" in stderr_output