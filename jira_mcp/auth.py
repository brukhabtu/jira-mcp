"""Jira authentication and HTTP client."""
from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from jira_mcp.config import JiraConfig
else:
    from jira_mcp.config import JiraConfig


class JiraClient:
    """Authenticated HTTP client for Jira API."""

    def __init__(self, config: JiraConfig) -> None:
        """Initialize the Jira client with configuration."""
        self.base_url = config.base_url
        self.user = config.user
        self.api_token = config.api_token
        self.timeout = config.timeout

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Jira API."""
        credentials = f"{self.user}:{self.api_token}"
        encoded_credentials = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

    async def get(self, path: str) -> Any:
        """Make an authenticated GET request to Jira API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, json: Any = None) -> Any:
        """Make an authenticated POST request to Jira API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, json: Any = None) -> Any:
        """Make an authenticated PUT request to Jira API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str) -> None:
        """Make an authenticated DELETE request to Jira API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
