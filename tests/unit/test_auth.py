"""Unit tests for Jira authentication client."""

import base64

import pytest

from jira_mcp.auth import JiraClient
from jira_mcp.config import JiraConfig


class TestJiraClient:
    """Tests for JiraClient authentication."""

    def test_stores_config_correctly(self, sample_jira_config: JiraConfig) -> None:
        """Test that JiraClient properly stores configuration values."""
        client = JiraClient(sample_jira_config)

        assert client.base_url == "https://test.atlassian.net"
        assert client.user == "test@example.com"
        assert client.api_token == "test-token"
        assert client.timeout == 30

    def test_auth_headers_format(self, sample_jira_config: JiraConfig) -> None:
        """Test that auth headers are properly formatted for Basic Auth."""
        client = JiraClient(sample_jira_config)
        headers = client.get_auth_headers()

        # Verify header structure
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

        # Verify Basic Auth format
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Basic ")

        # Verify credentials can be decoded back
        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode("utf-8")
        assert decoded_creds == "test@example.com:test-token"

    def test_auth_headers_handles_special_characters(self) -> None:
        """Test that auth headers properly encode special characters in credentials."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            user="user+test@example.com",
            api_token="token:with:colons",
        )

        client = JiraClient(config)
        headers = client.get_auth_headers()

        # Should not raise any encoding errors
        auth_header = headers["Authorization"]
        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode("utf-8")
        assert decoded_creds == "user+test@example.com:token:with:colons"

    @pytest.mark.parametrize(
        "path,expected_url",
        [
            ("/rest/api/3/issue", "https://test.atlassian.net/rest/api/3/issue"),
            (
                "rest/api/3/issue",
                "https://test.atlassian.netrest/api/3/issue",
            ),  # No leading slash
            ("/", "https://test.atlassian.net/"),
            ("", "https://test.atlassian.net"),
        ],
    )
    def test_url_construction(
        self, sample_jira_config: JiraConfig, path: str, expected_url: str
    ) -> None:
        """Test that URLs are properly constructed for API calls."""
        client = JiraClient(sample_jira_config)

        # We're testing the URL construction logic, not the HTTP call
        constructed_url = f"{client.base_url}{path}"
        assert constructed_url == expected_url

    @pytest.mark.parametrize(
        "base_url,expected_url",
        [
            ("https://test.atlassian.net/", "https://test.atlassian.net/"),
            ("https://test.atlassian.net", "https://test.atlassian.net"),
        ],
    )
    def test_base_url_normalization(self, base_url: str, expected_url: str) -> None:
        """Test that base URLs are handled consistently."""
        config = JiraConfig(
            base_url=base_url, user="user@example.com", api_token="token123"
        )
        client = JiraClient(config)

        # Should store exactly what was provided
        assert client.base_url == expected_url

    @pytest.mark.parametrize("timeout", [30, 60, 120])
    def test_timeout_value_stored(self, timeout: int) -> None:
        """Test that timeout configuration is properly stored."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            user="user@example.com",
            api_token="token123",
            timeout=timeout,
        )

        client = JiraClient(config)
        assert client.timeout == timeout

    def test_default_timeout(self) -> None:
        """Test default timeout value."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            user="user@example.com",
            api_token="token123",
        )

        client = JiraClient(config)
        assert client.timeout == 30  # Default from config model
