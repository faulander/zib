# Backend Dockerfile for Zib RSS Reader
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy uv files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/zib.db
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false
ENV RELOAD=false
ENV DOCKER_CONTAINER=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)"

# Run the application with migrations
CMD ["./start.sh"]
