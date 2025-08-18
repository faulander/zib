#!/bin/bash
set -e

echo "Starting Zib RSS Reader Backend..."

# Initialize database tables
echo "Initializing database..."
uv run python init_db.py

# Run database migrations
echo "Running database migrations..."
uv run python run_migrations.py

# Start the application
echo "Starting FastAPI application..."
exec uv run python -m app.main