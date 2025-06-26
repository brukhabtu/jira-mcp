"""Settings models for Jira MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    pass


class JiraSettings(BaseSettings):
    """Settings for Jira connection."""

    base_url: str
    user: str = Field(alias="JIRA_API_USER")
    api_token: str = Field(alias="JIRA_API_TOKEN")
    timeout: int = 30
    openapi_spec_path: str | None = None

    model_config = {
        "env_prefix": "JIRA_",
        "populate_by_name": True,
    }

    @field_validator("base_url", "user", "api_token")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "Field cannot be empty"
            raise ValueError(msg)
        return v.strip()


class MCPSettings(BaseSettings):
    """Settings for MCP server."""

    transport: str = "stdio"
    port: int = 8000
    log_level: str = "INFO"
    route_config_path: str = "./route-configs.yaml"
    route_config_name: str = "read-only-plus"

    model_config = {"env_prefix": "MCP_"}


class AppSettings(BaseSettings):
    """Main application settings."""

    jira: JiraSettings
    mcp: MCPSettings

    def __init__(self, **kwargs):
        """Initialize AppSettings with environment variables."""
        if 'jira' not in kwargs:
            kwargs['jira'] = JiraSettings()
        if 'mcp' not in kwargs:
            kwargs['mcp'] = MCPSettings()
        super().__init__(**kwargs)
