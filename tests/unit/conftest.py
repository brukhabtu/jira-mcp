"""Shared test fixtures for unit tests."""

import os
from collections.abc import Iterator

import pytest

from jira_mcp.settings import AppSettings, JiraSettings, MCPSettings


@pytest.fixture
def sample_jira_settings() -> JiraSettings:
    """Create a sample JiraSettings for testing."""
    return JiraSettings(
        base_url="https://test.atlassian.net",
        user="test@example.com",
        api_token="test-token",
        timeout=30,
    )


@pytest.fixture
def sample_mcp_settings() -> MCPSettings:
    """Create a sample MCPSettings for testing."""
    return MCPSettings(
        transport="stdio",
        port=8000,
        log_level="INFO",
    )


@pytest.fixture
def sample_app_settings(
    sample_jira_settings: JiraSettings, sample_mcp_settings: MCPSettings
) -> AppSettings:
    """Create a sample AppSettings for testing."""
    return AppSettings(jira=sample_jira_settings, mcp=sample_mcp_settings)


@pytest.fixture
def clean_env() -> Iterator[None]:
    """Ensure clean environment variables for testing."""
    # Store original values
    original_values = {}
    test_vars = [
        "JIRA_BASE_URL",
        "JIRA_USER",
        "JIRA_API_TOKEN",
        "JIRA_TIMEOUT",
        "MCP_TRANSPORT",
        "MCP_PORT",
        "MCP_LOG_LEVEL",
    ]

    for var in test_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]
        if var in original_values:
            os.environ[var] = original_values[var]


@pytest.fixture
def test_env_vars() -> Iterator[dict[str, str]]:
    """Set up test environment variables."""
    test_values = {
        "JIRA_BASE_URL": "https://test.atlassian.net",
        "JIRA_USER": "test@example.com",
        "JIRA_API_TOKEN": "test-token",
    }

    # Store original values
    original_values = {}
    for var, value in test_values.items():
        if var in os.environ:
            original_values[var] = os.environ[var]
        os.environ[var] = value

    yield test_values

    # Clean up
    for var in test_values:
        if var in os.environ:
            del os.environ[var]
        if var in original_values:
            os.environ[var] = original_values[var]
