"""Unit tests for the main module."""
import sys
from pathlib import Path

# Add project root to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMainModule:
    """Unit tests for main module functionality."""

    def test_main_module_exists(self) -> None:
        """Test that the main module can be imported."""
        import jira_mcp.__main__

        assert hasattr(jira_mcp.__main__, "main")

    def test_main_function_callable(self) -> None:
        """Test that the main function exists and is callable."""
        from jira_mcp.__main__ import main

        assert callable(main)

    def test_package_importable(self) -> None:
        """Test that the jira_mcp package can be imported."""
        import jira_mcp

        assert jira_mcp.__version__ == "0.1.0"

    def test_setup_logging_function_exists(self) -> None:
        """Test that setup_logging function exists and is callable."""
        from jira_mcp.__main__ import setup_logging

        assert callable(setup_logging)

    def test_setup_logging_returns_logger(self) -> None:
        """Test that setup_logging returns a logger instance."""
        import logging

        from jira_mcp.__main__ import setup_logging

        logger = setup_logging("stdio")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "jira_mcp"
