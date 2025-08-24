# Multi-stage build for optimized image size and runtime performance
FROM python:3.12-slim as builder

# Install UV for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set build-time environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create build directory
WORKDIR /build

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
RUN uv sync --frozen --no-install-project --no-dev --compile-bytecode

# Copy source code
COPY src/ ./src/

# Install the project
RUN uv sync --frozen --no-dev --compile-bytecode

# Production runtime stage
FROM python:3.12-slim as runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r stockagent && useradd -r -g stockagent -d /app -s /bin/bash stockagent

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8080

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=stockagent:stockagent /build/.venv /app/.venv

# Copy source code
COPY --from=builder --chown=stockagent:stockagent /build/src /app/src

# Copy configuration files
COPY --chown=stockagent:stockagent firebase_creds.json /app/
COPY --chown=stockagent:stockagent .dev.env /app/.env

# Create directory for database mounting
RUN mkdir -p /app/data && chown stockagent:stockagent /app/data

# Create directory for logs
RUN mkdir -p /app/logs && chown stockagent:stockagent /app/logs

# Switch to non-root user
USER stockagent

# Expose the application port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default command
CMD ["python", "-m", "stock_agent.main"]

# Build-time labels for metadata
LABEL org.opencontainers.image.title="Stock Agent" \
    org.opencontainers.image.description="Stock monitoring and notification service" \
    org.opencontainers.image.version="0.1.0" \
    org.opencontainers.image.authors="Stock Agent Team" \
    org.opencontainers.image.source="https://github.com/your-repo/stock-agent"
