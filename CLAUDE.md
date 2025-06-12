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

# Server Commands
uv run jira-mcp --help                    # Show server help
uv run jira-mcp --transport http --port 8080  # Run on HTTP transport
```

### Package Management
Use `uv add` instead of editing pyproject.toml directly:
```bash
uv add package-name
uv add --dev dev-package-name
```

### Docker
```bash
# Build Docker image with CI dependencies
docker build --build-arg BUILD_ENV=ci -t jira-mcp .

# Run with environment variables  
docker run -e JIRA_BASE_URL=https://company.atlassian.net \
           -e JIRA_API_USER=user@company.com \
           -e JIRA_API_TOKEN=token \
           jira-mcp

# Use published image
docker run ghcr.io/brukhabtu/jira-mcp:latest
```

## Architecture

This is a Jira MCP server built with FastMCP 2.0's OpenAPI integration. The project generates MCP tools from Jira's OpenAPI specification (bundled for reliability), providing access to Jira API while implementing security-focused route filtering.

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

### Security and Route Filtering

The server implements a security-first approach with configurable filtering:

**Default Security Model (RECOMMENDED):**
1. **DENY ALL** destructive operations (POST, PUT, PATCH, DELETE)
2. **ALLOW ONLY** specific safe read-only GET endpoints
3. **DEFAULT DENY** everything else

**Whitelisted Safe Endpoints:**
- Core issue management (get, search, comments, history, worklog)
- Project information (projects, issue types, statuses, priorities, resolutions)
- Agile data (boards, sprints)
- User and team information (users, groups)
- Dashboards and filters
- Safe system metadata (server info, custom fields)

**Security Configuration:**
- `MCP_ENABLE_SECURITY_FILTERING=true` (default): Only safe endpoints exposed
- `MCP_ENABLE_SECURITY_FILTERING=false`: **WARNING** - Exposes ALL Jira API endpoints including destructive operations

### Required Environment Variables
- `JIRA_BASE_URL`: Your Jira instance URL (e.g., `https://company.atlassian.net`)
- `JIRA_API_USER`: Your Jira username/email address  
- `JIRA_API_TOKEN`: Your Jira API token

### Optional Environment Variables
- `JIRA_TIMEOUT`: HTTP timeout in seconds (default: 30)
- `JIRA_OPENAPI_SPEC_PATH`: Path to custom OpenAPI spec file (default: uses bundled spec)
- `MCP_TRANSPORT`: Transport method - stdio, http, sse (default: stdio)
- `MCP_PORT`: Port for HTTP/SSE transport (default: 8000)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)
- `MCP_ENABLE_SECURITY_FILTERING`: Enable security filtering (default: true)

### CI/CD and Testing

**GitHub Actions Pipeline:**
- Builds and pushes Docker images to GHCR (`ghcr.io/brukhabtu/jira-mcp`)
- All CI steps run in containers for consistency
- Multi-stage Docker build with production and CI targets

**Testing Architecture:**
- **`tests/unit/`**: Unit tests for individual components with mocking
- **`tests/integration/`**: Integration tests including CLI and server initialization  
- **Test fixtures**: Shared in `conftest.py` files for test configuration and Jira client mocking

### Async Initialization Pattern

The server uses a two-phase initialization:
1. **`__init__()`**: Synchronous setup with configuration
2. **`initialize()`**: Async initialization that fetches OpenAPI spec and creates authenticated client
3. **`run()`**: Synchronous MCP server execution