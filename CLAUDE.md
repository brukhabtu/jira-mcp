# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install dependencies  
uv sync

# Run the server
uv run python -m jira_mcp --help

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=jira_mcp

# Type checking
uv run mypy src/

# Code formatting and linting
uv run ruff check .
uv run ruff format .
```

### Package Management
Use `uv add` instead of editing pyproject.toml directly:
```bash
uv add package-name
uv add --dev dev-package-name
```

## Architecture

This is a Jira MCP server built with FastMCP 2.0's OpenAPI integration. The project uses the OpenAPI specification from Jira's REST API to automatically generate MCP tools and resources, eliminating code duplication and providing automatic schema validation.

### Key Design Patterns
- **Configuration**: YAML files with `!env` tags for environment variable substitution
- **FastMCP Integration**: Uses `FastMCP.from_openapi()` for automatic server generation
- **Transport Support**: stdio (default), HTTP, and SSE transports

### Project Structure
```
src/jira_mcp/
├── __init__.py         # Package version
└── __main__.py         # CLI entry point with argument parsing
```

### Configuration Format
Uses YAML configuration with environment variable support:
```yaml
jira:
  base_url: !env JIRA_BASE_URL
  user: !env JIRA_API_USER  
  api_token: !env JIRA_API_TOKEN
  timeout: 30

mcp:
  transport: stdio
  port: 8000
  log_level: INFO
```

### Required Environment Variables
- `JIRA_BASE_URL`: Your Jira instance URL
- `JIRA_API_USER`: Your Jira username/email address  
- `JIRA_API_TOKEN`: Your Jira API token

### Optional Environment Variables
- `MCP_TRANSPORT`: Transport method (stdio, http, sse)
- `MCP_PORT`: Port for HTTP/SSE transport
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Development Notes

- Entry point supports --config, --transport, and --port flags
- Currently in early development stage - main server functionality not yet implemented
- Uses modern Python tooling: uv, ruff, mypy, pytest
- Follows TDD approach with pytest for testing
- Uses strict mypy type checking with Python 3.11+