"""Unit tests for settings models and loading."""

import os

import pytest

from jira_mcp.settings import AppSettings, JiraSettings, MCPSettings


class TestJiraSettings:
    """Tests for JiraSettings model."""

    def test_model_creation_and_defaults(self, sample_jira_settings: JiraSettings) -> None:
        """Test JiraSettings model creation and default values."""
        assert sample_jira_settings.base_url == "https://test.atlassian.net"
        assert sample_jira_settings.user == "test@example.com"
        assert sample_jira_settings.api_token == "test-token"
        assert sample_jira_settings.timeout == 30  # default value

    def test_validation_rejects_empty_values(self) -> None:
        """Test that JiraSettings properly validates required fields."""
        # Empty base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraSettings(base_url="", user="test@example.com", api_token="token")

        # Whitespace-only base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraSettings(base_url="   ", user="test@example.com", api_token="token")

        # Empty user
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraSettings(
                base_url="https://test.atlassian.net", user="", api_token="token"
            )

        # Empty API token
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraSettings(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="",
            )

    def test_strips_whitespace(self) -> None:
        """Test that JiraSettings strips whitespace from string fields."""
        config = JiraSettings(
            base_url="  https://test.atlassian.net  ",
            user="  test@example.com  ",
            api_token="  token123  ",
        )

        assert config.base_url == "https://test.atlassian.net"
        assert config.user == "test@example.com"
        assert config.api_token == "token123"


class TestMCPSettings:
    """Tests for MCPSettings model."""

    def test_model_creation_and_defaults(self, sample_mcp_settings: MCPSettings) -> None:
        """Test MCPSettings model creation and default values."""
        assert sample_mcp_settings.transport == "stdio"
        assert sample_mcp_settings.port == 8000
        assert sample_mcp_settings.log_level == "INFO"

    def test_custom_values(self) -> None:
        """Test MCPSettings accepts custom values."""
        config = MCPSettings(transport="sse", port=9000, log_level="DEBUG")

        assert config.transport == "sse"
        assert config.port == 9000
        assert config.log_level == "DEBUG"

    def test_defaults_when_not_specified(self) -> None:
        """Test that MCPSettings has sensible defaults."""
        config = MCPSettings()

        assert config.transport == "stdio"
        assert config.port == 8000
        assert config.log_level == "INFO"


class TestAppSettings:
    """Tests for AppSettings model."""

    def test_model_creation(self, sample_app_settings: AppSettings) -> None:
        """Test AppSettings model creation."""
        assert sample_app_settings.jira.base_url == "https://test.atlassian.net"
        assert sample_app_settings.mcp.transport == "stdio"

    def test_from_env_with_required_vars(self, test_env_vars: dict[str, str]) -> None:
        """Test loading configuration from environment variables."""
        config = AppSettings()

        assert config.jira.base_url == "https://test.atlassian.net"
        assert config.jira.user == "test@example.com"
        assert config.jira.api_token == "test-token"
        assert config.jira.timeout == 30  # default
        assert config.mcp.transport == "stdio"  # default
        assert config.mcp.port == 8000  # default
        assert config.mcp.log_level == "INFO"  # default

    def test_from_env_with_custom_values(self, clean_env: None) -> None:
        """Test loading configuration with custom environment variables."""
        # Set test environment variables including optional ones
        os.environ["JIRA_BASE_URL"] = "https://custom.atlassian.net"
        os.environ["JIRA_USER"] = "custom@example.com"
        os.environ["JIRA_API_TOKEN"] = "custom-token"
        os.environ["JIRA_TIMEOUT"] = "60"
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_PORT"] = "9000"
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"

        config = AppSettings()

        assert config.jira.base_url == "https://custom.atlassian.net"
        assert config.jira.user == "custom@example.com"
        assert config.jira.api_token == "custom-token"
        assert config.jira.timeout == 60
        assert config.mcp.transport == "http"
        assert config.mcp.port == 9000
        assert config.mcp.log_level == "DEBUG"

    def test_from_env_missing_required_vars(self, clean_env: None) -> None:
        """Test error when required environment variables are missing."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError, match="Field required"):
            AppSettings()

        # Test missing user
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        with pytest.raises(ValidationError, match="Field required"):
            AppSettings()

        # Test missing token
        os.environ["JIRA_USER"] = "test@example.com"
        with pytest.raises(ValidationError, match="Field required"):
            AppSettings()

    def test_env_var_edge_cases(self, clean_env: None) -> None:
        """Test edge cases in environment variable handling."""
        # Test with values that have colons (common in URLs and tokens)
        os.environ["JIRA_BASE_URL"] = "https://custom.atlassian.net:8080"
        os.environ["JIRA_USER"] = "user:with:colons@example.com"
        os.environ["JIRA_API_TOKEN"] = "token:with:colons:value"

        config = AppSettings()
        assert config.jira.base_url == "https://custom.atlassian.net:8080"
        assert config.jira.user == "user:with:colons@example.com"
        assert config.jira.api_token == "token:with:colons:value"

    def test_env_var_type_conversion(self, clean_env: None) -> None:
        """Test that environment variables are properly converted to expected types."""
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_USER"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "token"
        os.environ["JIRA_TIMEOUT"] = "120"
        os.environ["MCP_PORT"] = "9090"

        config = AppSettings()

        # Verify types are correct
        assert isinstance(config.jira.timeout, int)
        assert isinstance(config.mcp.port, int)
        assert config.jira.timeout == 120
        assert config.mcp.port == 9090

    def test_invalid_numeric_env_vars(self, clean_env: None) -> None:
        """Test that invalid numeric environment variables cause errors."""
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_USER"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "token"
        os.environ["JIRA_TIMEOUT"] = "not-a-number"

        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AppSettings()
