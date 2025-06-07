"""Configuration models for Jira MCP server."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    pass


class JiraConfig(BaseModel):
    """Configuration for Jira connection."""

    base_url: str
    user: str
    api_token: str
    timeout: int = 30
    openapi_spec_path: str | None = None

    @field_validator("base_url", "user", "api_token")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "Field cannot be empty"
            raise ValueError(msg)
        return v.strip()


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    transport: str = "stdio"
    port: int = 8000
    log_level: str = "INFO"
    enable_security_filtering: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""

    jira: JiraConfig
    mcp: MCPConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables."""
        # Required environment variables
        base_url = os.getenv("JIRA_BASE_URL")
        user = os.getenv("JIRA_API_USER")
        api_token = os.getenv("JIRA_API_TOKEN")

        if not base_url:
            msg = "JIRA_BASE_URL environment variable is required"
            raise ValueError(msg)
        if not user:
            msg = "JIRA_API_USER environment variable is required"
            raise ValueError(msg)
        if not api_token:
            msg = "JIRA_API_TOKEN environment variable is required"
            raise ValueError(msg)

        # Optional environment variables with defaults
        timeout = int(os.getenv("JIRA_TIMEOUT", "30"))
        openapi_spec_path = os.getenv("JIRA_OPENAPI_SPEC_PATH")
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        port = int(os.getenv("MCP_PORT", "8000"))
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        enable_security_filtering = os.getenv(
            "MCP_ENABLE_SECURITY_FILTERING", "true"
        ).lower() in ("true", "1", "yes")

        jira_config = JiraConfig(
            base_url=base_url,
            user=user,
            api_token=api_token,
            timeout=timeout,
            openapi_spec_path=openapi_spec_path,
        )

        mcp_config = MCPConfig(
            transport=transport,
            port=port,
            log_level=log_level,
            enable_security_filtering=enable_security_filtering,
        )

        return cls(jira=jira_config, mcp=mcp_config)
