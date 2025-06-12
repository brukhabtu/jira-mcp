# Jira MCP Server

A Jira MCP server that uses FastMCP 2.0's OpenAPI integration to expose Jira functionality through the Model Context Protocol (MCP).

## Features

- **OpenAPI integration** - Generates MCP tools from Jira's API specification
- **Secure authentication** - Uses Jira API tokens
- **Multiple transports** - Support for stdio, HTTP, and SSE protocols
- **Security filtering** - Only exposes read-only endpoints by default
- **Type-safe** - Built with Python type hints and Pydantic models

## Quick Start

### 1. Setup Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create an API token
3. Note your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)

### 2. Set Environment Variables

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_API_USER="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

### 3. Run with Docker (Recommended)

```bash
docker run -e JIRA_BASE_URL=https://yourcompany.atlassian.net \
           -e JIRA_API_USER=your-email@company.com \
           -e JIRA_API_TOKEN=your-api-token \
           ghcr.io/brukhabtu/jira-mcp:latest
```

## How It Works

The server:

1. Downloads Jira's OpenAPI specification
2. Generates MCP tools for Jira API endpoints
3. Authenticates requests using your API token
4. Applies security filtering to expose only safe operations

Available functionality:
- Issue reading and search
- Project information
- User and team data
- Agile boards and sprints
- Dashboards and filters

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_BASE_URL` | ✅ | - | Your Jira instance URL (e.g., `https://company.atlassian.net`) |
| `JIRA_API_USER` | ✅ | - | Your Jira username/email address |
| `JIRA_API_TOKEN` | ✅ | - | Your Jira API token |
| `JIRA_TIMEOUT` | ❌ | `30` | HTTP timeout in seconds |
| `JIRA_OPENAPI_SPEC_PATH` | ❌ | bundled | Path to custom OpenAPI spec file |
| `MCP_TRANSPORT` | ❌ | `stdio` | Transport method (`stdio`, `http`, `sse`) |
| `MCP_PORT` | ❌ | `8000` | Port for HTTP/SSE transports |
| `MCP_LOG_LEVEL` | ❌ | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MCP_ENABLE_SECURITY_FILTERING` | ❌ | `true` | Enable security filtering (blocks destructive operations) |

### Command Line Options

```bash
jira-mcp [OPTIONS]

Options:
  --transport {stdio,http,sse} Transport method (overrides MCP_TRANSPORT env var)
  --port PORT                  Port for HTTP/SSE transport (overrides MCP_PORT env var)
  --version                    Show version and exit
  --help                       Show help message
```

## Integration with MCP Clients

### Claude Desktop (Recommended)

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "JIRA_BASE_URL=https://yourcompany.atlassian.net",
        "--env", "JIRA_API_USER=your-email@company.com", 
        "--env", "JIRA_API_TOKEN=your-api-token",
        "ghcr.io/brukhabtu/jira-mcp:latest"
      ]
    }
  }
}
```

For enhanced security, set credentials as environment variables in your shell profile:
```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_API_USER="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

Then use:
```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "JIRA_BASE_URL",
        "--env", "JIRA_API_USER",
        "--env", "JIRA_API_TOKEN", 
        "ghcr.io/brukhabtu/jira-mcp:latest"
      ]
    }
  }
}
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Type checking and linting
uv run mypy jira_mcp/
uv run ruff check .
uv run ruff format .
```

### Architecture

- **`jira_mcp/config.py`**: Pydantic models with environment variable loading
- **`jira_mcp/auth.py`**: HTTP client with Jira Basic Auth
- **`jira_mcp/server.py`**: FastMCP integration with OpenAPI spec fetching
- **`jira_mcp/__main__.py`**: CLI interface with environment-based configuration

## Troubleshooting

### Common Issues

**"Configuration error" on startup**: Check that all required environment variables (`JIRA_BASE_URL`, `JIRA_API_USER`, `JIRA_API_TOKEN`) are set.

**Authentication errors**: Verify your API token is correct and your email matches your Jira account.

**Connection timeout**: Check your `JIRA_BASE_URL` is correct and accessible. Increase `JIRA_TIMEOUT` if needed.

**Claude Desktop not finding server**: Ensure environment variables are available to GUI applications (may require restart or `launchctl setenv` on macOS).

### Getting Help

- Check the [CLAUDE.md](./CLAUDE.md) file for development guidance
- Review test files for usage examples
- Run `jira-mcp --help` for command line options

## Security

### Security Filtering

**Default Security Model:**
- Blocks all destructive operations (POST, PUT, PATCH, DELETE)
- Allows only safe read-only GET endpoints
- Default deny for everything else

**Endpoints Exposed:**
- Issue reading and search
- Project metadata
- User and team information
- Agile boards and sprint data
- Dashboards and saved filters
- System information and field metadata

**Configuration:**
```bash
# Default: Security filtering enabled
MCP_ENABLE_SECURITY_FILTERING=true

# Disable filtering (exposes all endpoints)
MCP_ENABLE_SECURITY_FILTERING=false  # Use with caution
```

### Additional Security Measures

- API tokens are stored in environment variables, never in code or config files
- All HTTP requests use TLS encryption
- No sensitive data is logged or exposed
- Follows OAuth 2.0 and Atlassian security best practices

## License

MIT