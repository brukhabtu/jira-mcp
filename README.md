# Jira MCP Server

A production-ready Jira MCP server using FastMCP 2.0's OpenAPI integration. Automatically exposes your entire Jira instance through the Model Context Protocol (MCP) with zero configuration overhead.

## Features

- 🚀 **Zero-maintenance OpenAPI integration** - Automatically generates MCP tools from Jira's official API specification
- 🔐 **Secure authentication** - Uses Jira API tokens with environment variable support
- 🌐 **Multiple transports** - Support for stdio, HTTP, and SSE protocols
- ⚡ **Fast and lightweight** - Minimal overhead with async HTTP client
- 🔧 **Production-ready** - Type-safe, well-tested, and follows security best practices
- 📝 **Self-documenting** - All Jira API endpoints automatically become available as MCP tools

## Quick Start

### 1. Installation

```bash
# Clone and install
git clone <repository-url>
cd jira_mcp
uv sync
```

### 2. Setup Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create an API token
3. Note your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)

### 3. Set Environment Variables

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_API_USER="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

### 4. Run the Server

```bash
# Default configuration (stdio transport)
jira-mcp

# Or with custom transport
jira-mcp --transport http --port 8080
```

## How It Works

The server automatically:

1. **Downloads** Jira's official OpenAPI specification
2. **Generates** MCP tools for every Jira API endpoint
3. **Authenticates** requests using your API token
4. **Exposes** your entire Jira instance through MCP

This means you get instant access to:
- Issue management (create, update, search, transition)
- Project administration
- User and permission management  
- Dashboards and filters
- Webhooks and automation
- And every other Jira Cloud API feature!

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_BASE_URL` | ✅ | - | Your Jira instance URL (e.g., `https://company.atlassian.net`) |
| `JIRA_API_USER` | ✅ | - | Your Jira username/email address |
| `JIRA_API_TOKEN` | ✅ | - | Your Jira API token |
| `JIRA_TIMEOUT` | ❌ | `30` | HTTP timeout in seconds |
| `MCP_TRANSPORT` | ❌ | `stdio` | Transport method (`stdio`, `http`, `sse`) |
| `MCP_PORT` | ❌ | `8000` | Port for HTTP/SSE transports |
| `MCP_LOG_LEVEL` | ❌ | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

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

### Claude Desktop

**Option 1: Use system environment variables (recommended)**

Add your credentials to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_API_USER="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

Then use a minimal Claude Desktop configuration:
```json
{
  "mcpServers": {
    "jira": {
      "command": "jira-mcp"
    }
  }
}
```

**Option 2: Specify environment variables in config**

```json
{
  "mcpServers": {
    "jira": {
      "command": "jira-mcp",
      "env": {
        "JIRA_BASE_URL": "https://yourcompany.atlassian.net",
        "JIRA_API_USER": "your-email@company.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

⚠️ **Security Note**: Option 1 is more secure as it keeps credentials out of config files.

### Other MCP Clients

The server supports all MCP transport protocols:

- **stdio**: For local desktop applications (Claude Desktop, etc.)
- **HTTP**: For web applications and remote clients
- **SSE**: For real-time web applications

## Development

### Setup

```bash
# Install dependencies
uv sync

# Run all tests (41 unit tests, 1 integration test)
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests  
uv run pytest tests/integration/

# Type checking (mypy strict mode)
uv run mypy jira_mcp/

# Code formatting and linting
uv run ruff check .
uv run ruff format .
```

### Architecture

- **`jira_mcp/config.py`**: Pydantic models with environment variable loading
- **`jira_mcp/auth.py`**: HTTP client with Jira Basic Auth
- **`jira_mcp/server.py`**: FastMCP integration with OpenAPI spec fetching
- **`jira_mcp/__main__.py`**: CLI interface with environment-based configuration

### Testing

The project includes 41 unit tests organized in `tests/unit/` covering:
- Configuration validation and edge cases
- Authentication and HTTP client behavior
- Server initialization and error handling
- Environment variable parsing and type conversion

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

- API tokens are stored in environment variables, never in code or config files
- All HTTP requests use TLS encryption
- No sensitive data is logged or exposed
- Follows OAuth 2.0 and Atlassian security best practices

## License

MIT