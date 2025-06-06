# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install dependencies  
uv sync

# Run the server
uv run python -m jira_mcp --help

# Run server with environment variables
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_API_USER="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
uv run python -m jira_mcp

# Run tests
uv run pytest

# Run specific test types
uv run pytest tests/unit/      # Unit tests only
uv run pytest tests/integration/  # Integration tests only

# Run tests with coverage
uv run pytest --cov=jira_mcp

# Type checking  
uv run mypy jira_mcp/

# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Run single test file
uv run pytest tests/unit/test_config.py -v
```

### Package Management
Use `uv add` instead of editing pyproject.toml directly:
```bash
uv add package-name
uv add --dev dev-package-name
```

### Docker
```bash
# Build Docker image
docker build -t jira-mcp .

# Run with environment variables
docker run -e JIRA_BASE_URL=https://company.atlassian.net \
           -e JIRA_API_USER=user@company.com \
           -e JIRA_API_TOKEN=token \
           jira-mcp
```

## Architecture

This is a production-ready Jira MCP server built with FastMCP 2.0's OpenAPI integration. The project automatically generates MCP tools from Jira's official OpenAPI specification, providing zero-maintenance access to the entire Jira API while implementing security-focused route filtering.

### Core Components

- **`jira_mcp/config.py`**: Pydantic models for configuration with environment variable loading and validation
- **`jira_mcp/auth.py`**: HTTP client with Jira Basic Auth using API tokens
- **`jira_mcp/server.py`**: FastMCP integration with OpenAPI spec fetching and security filtering
- **`jira_mcp/__main__.py`**: CLI interface with environment-based configuration and logging

### Key Design Patterns

- **Environment-based Configuration**: Uses Pydantic models with `from_env()` class method for environment variable loading
- **FastMCP OpenAPI Integration**: Uses `FastMCP.from_openapi()` to automatically generate tools from Jira's API specification
- **Security-First Route Filtering**: Implements `RouteMap` filters to expose only read-only endpoints by default
- **Transport Flexibility**: Support for stdio (default), HTTP, and SSE transports
- **Authenticated HTTP Client**: Pre-configured httpx client with Basic Auth for all Jira API requests

### Route Filtering Strategy

The server implements a security-focused approach:
- **Excludes all destructive operations** (POST, PUT, PATCH, DELETE) by default
- **Includes specific read-only patterns** for engineering teams:
  - Issue retrieval (`/rest/api/3/issue/{id}`)
  - Issue search (`/rest/api/3/search`)
  - Project information (`/rest/api/3/project.*`)
  - Board and sprint data (`/rest/api/3/board.*`, `/rest/api/3/sprint.*`)
  - User information (`/rest/api/3/user.*`)
  - Comments, changelog, and worklog (read-only)
  - Dashboards and filters

### Required Environment Variables
- `JIRA_BASE_URL`: Your Jira instance URL (e.g., `https://company.atlassian.net`)
- `JIRA_API_USER`: Your Jira username/email address  
- `JIRA_API_TOKEN`: Your Jira API token

### Optional Environment Variables
- `JIRA_TIMEOUT`: HTTP timeout in seconds (default: 30)
- `MCP_TRANSPORT`: Transport method - stdio, http, sse (default: stdio)
- `MCP_PORT`: Port for HTTP/SSE transport (default: 8000)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)

### Testing Architecture

The project has 55+ tests organized in:
- **`tests/unit/`**: Unit tests for individual components with mocking
- **`tests/integration/`**: Integration tests including CLI and server initialization
- **Test fixtures**: Shared in `conftest.py` files for test configuration and Jira client mocking

### Async Initialization Pattern

The server uses a two-phase initialization:
1. **`__init__()`**: Synchronous setup with configuration
2. **`initialize()`**: Async initialization that fetches OpenAPI spec and creates authenticated client
3. **`run()`**: Synchronous MCP server execution