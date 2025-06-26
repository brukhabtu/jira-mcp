# Multi-stage Dockerfile for Jira MCP Server
ARG PYTHON_VERSION=3.12
ARG BUILD_ENV=production

# Base image with security updates
FROM python:${PYTHON_VERSION}-slim AS base
ARG BUILD_ENV

# Validate BUILD_ENV argument
RUN if [ "$BUILD_ENV" != "production" ] && [ "$BUILD_ENV" != "ci" ]; then \
        echo "Invalid BUILD_ENV: $BUILD_ENV. Must be 'production' or 'ci'" && exit 1; \
    fi

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Create non-root user early (shared across stages)
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Builder stage
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

# Switch to app user and set working directory in user's home
USER app
WORKDIR /home/app/build

# Configure uv to use user cache
ENV UV_CACHE_DIR=/home/app/.cache/uv

# Copy dependency files first (better caching)
COPY --chown=app:app pyproject.toml uv.lock ./

# Install dependencies based on build environment
RUN if [ "$BUILD_ENV" = "ci" ]; then \
        uv sync --frozen --no-install-project --dev; \
    else \
        uv sync --frozen --no-install-project; \
    fi

# Copy source code
COPY --chown=app:app . .

# Install the application
RUN uv pip install --no-deps .

# Production stage
FROM base AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv in production (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

# Switch to app user (created in base stage)
USER app
WORKDIR /home/app

# Configure uv cache for production user
ENV UV_CACHE_DIR=/home/app/.cache/uv

# Copy virtual environment and app from builder
COPY --from=builder --chown=app:app /home/app/build/.venv ./.venv
COPY --from=builder --chown=app:app /home/app/build/jira_mcp ./jira_mcp

# Copy tests and config files for CI builds
COPY --from=builder --chown=app:app /home/app/build/tests ./tests
COPY --from=builder --chown=app:app /home/app/build/pyproject.toml ./pyproject.toml
COPY --from=builder --chown=app:app /home/app/build/README.md ./README.md

# Set up PATH for virtual environment
ENV PATH="/home/app/.venv/bin:$PATH"
ENV PYTHONPATH="/home/app"

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set entrypoint to uv run
ENTRYPOINT ["uv", "run"]

# Default command to start MCP server
CMD ["python", "-m", "jira_mcp"]

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD uv run python -c "import jira_mcp; print('OK')" || exit 1

# Metadata labels
LABEL org.opencontainers.image.title="Jira MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Jira integration"
LABEL org.opencontainers.image.vendor="Bruk Habtu"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/brukhabtu/jira-mcp"