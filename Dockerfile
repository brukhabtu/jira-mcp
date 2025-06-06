# Use Python slim image as base
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# Multi-stage build: production image
FROM python:3.12-slim as production

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application code
COPY --chown=app:app . .

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Install the application
RUN /app/.venv/bin/python -m pip install --no-deps .

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import jira_mcp; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "jira_mcp"]

# Labels
LABEL org.opencontainers.image.title="Jira MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Jira integration"
LABEL org.opencontainers.image.vendor="Engineering Team"
LABEL org.opencontainers.image.licenses="MIT"