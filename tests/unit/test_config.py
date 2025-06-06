"""Unit tests for configuration models and loading."""

import os

import pytest

from jira_mcp.config import AppConfig, JiraConfig, MCPConfig


class TestJiraConfig:
    """Tests for JiraConfig model."""

    def test_model_creation_and_defaults(self, sample_jira_config: JiraConfig) -> None:
        """Test JiraConfig model creation and default values."""
        assert sample_jira_config.base_url == "https://test.atlassian.net"
        assert sample_jira_config.user == "test@example.com"
        assert sample_jira_config.api_token == "test-token"
        assert sample_jira_config.timeout == 30  # default value

    def test_validation_rejects_empty_values(self) -> None:
        """Test that JiraConfig properly validates required fields."""
        # Empty base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraConfig(base_url="", user="test@example.com", api_token="token")

        # Whitespace-only base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraConfig(base_url="   ", user="test@example.com", api_token="token")

        # Empty user
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraConfig(
                base_url="https://test.atlassian.net", user="", api_token="token"
            )

        # Empty API token
        with pytest.raises(ValueError, match="Field cannot be empty"):
            JiraConfig(
                base_url="https://test.atlassian.net",
                user="test@example.com",
                api_token="",
            )

    def test_strips_whitespace(self) -> None:
        """Test that JiraConfig strips whitespace from string fields."""
        config = JiraConfig(
            base_url="  https://test.atlassian.net  ",
            user="  test@example.com  ",
            api_token="  token123  ",
        )

        assert config.base_url == "https://test.atlassian.net"
        assert config.user == "test@example.com"
        assert config.api_token == "token123"


class TestMCPConfig:
    """Tests for MCPConfig model."""

    def test_model_creation_and_defaults(self, sample_mcp_config: MCPConfig) -> None:
        """Test MCPConfig model creation and default values."""
        assert sample_mcp_config.transport == "stdio"
        assert sample_mcp_config.port == 8000
        assert sample_mcp_config.log_level == "INFO"

    def test_custom_values(self) -> None:
        """Test MCPConfig accepts custom values."""
        config = MCPConfig(transport="sse", port=9000, log_level="DEBUG")

        assert config.transport == "sse"
        assert config.port == 9000
        assert config.log_level == "DEBUG"

    def test_defaults_when_not_specified(self) -> None:
        """Test that MCPConfig has sensible defaults."""
        config = MCPConfig()

        assert config.transport == "stdio"
        assert config.port == 8000
        assert config.log_level == "INFO"


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_model_creation(self, sample_app_config: AppConfig) -> None:
        """Test AppConfig model creation."""
        assert sample_app_config.jira.base_url == "https://test.atlassian.net"
        assert sample_app_config.mcp.transport == "stdio"

    def test_from_env_with_required_vars(self, test_env_vars: dict[str, str]) -> None:
        """Test loading configuration from environment variables."""
        config = AppConfig.from_env()

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
        os.environ["JIRA_API_USER"] = "custom@example.com"
        os.environ["JIRA_API_TOKEN"] = "custom-token"
        os.environ["JIRA_TIMEOUT"] = "60"
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_PORT"] = "9000"
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"

        config = AppConfig.from_env()

        assert config.jira.base_url == "https://custom.atlassian.net"
        assert config.jira.user == "custom@example.com"
        assert config.jira.api_token == "custom-token"
        assert config.jira.timeout == 60
        assert config.mcp.transport == "http"
        assert config.mcp.port == 9000
        assert config.mcp.log_level == "DEBUG"

    def test_from_env_missing_required_vars(self, clean_env: None) -> None:
        """Test error when required environment variables are missing."""
        with pytest.raises(
            ValueError, match="JIRA_BASE_URL environment variable is required"
        ):
            AppConfig.from_env()

        # Test missing user
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        with pytest.raises(
            ValueError, match="JIRA_API_USER environment variable is required"
        ):
            AppConfig.from_env()

        # Test missing token
        os.environ["JIRA_API_USER"] = "test@example.com"
        with pytest.raises(
            ValueError, match="JIRA_API_TOKEN environment variable is required"
        ):
            AppConfig.from_env()

    def test_env_var_edge_cases(self, clean_env: None) -> None:
        """Test edge cases in environment variable handling."""
        # Test with values that have colons (common in URLs and tokens)
        os.environ["JIRA_BASE_URL"] = "https://custom.atlassian.net:8080"
        os.environ["JIRA_API_USER"] = "user:with:colons@example.com"
        os.environ["JIRA_API_TOKEN"] = "token:with:colons:value"

        config = AppConfig.from_env()
        assert config.jira.base_url == "https://custom.atlassian.net:8080"
        assert config.jira.user == "user:with:colons@example.com"
        assert config.jira.api_token == "token:with:colons:value"

    def test_env_var_type_conversion(self, clean_env: None) -> None:
        """Test that environment variables are properly converted to expected types."""
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_API_USER"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "token"
        os.environ["JIRA_TIMEOUT"] = "120"
        os.environ["MCP_PORT"] = "9090"

        config = AppConfig.from_env()

        # Verify types are correct
        assert isinstance(config.jira.timeout, int)
        assert isinstance(config.mcp.port, int)
        assert config.jira.timeout == 120
        assert config.mcp.port == 9090

    def test_invalid_numeric_env_vars(self, clean_env: None) -> None:
        """Test that invalid numeric environment variables cause errors."""
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_API_USER"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "token"
        os.environ["JIRA_TIMEOUT"] = "not-a-number"

        with pytest.raises(ValueError):
            AppConfig.from_env()
