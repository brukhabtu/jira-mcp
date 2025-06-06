"""Shared test fixtures for integration tests."""

import pytest


@pytest.fixture(scope="session")
def integration_config():
    """Configuration for integration tests."""
    # This would typically load test-specific configuration
    # for integration tests that might need real services
    return {
        "test_timeout": 30,
        "mock_external_services": True,
    }
