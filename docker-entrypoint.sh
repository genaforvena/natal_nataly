#!/bin/bash
# Startup script for natal_nataly Docker container
# Runs database migrations before starting the application

set -e  # Exit on error

# If arguments are provided, execute them directly (for testing/debugging)
if [ $# -gt 0 ]; then
    exec "$@"
fi

echo "=== natal_nataly startup script ==="
echo ""

# Check if DATABASE_URL is set (PostgreSQL) or use SQLite
if [ -n "$DATABASE_URL" ]; then
    echo "Database: PostgreSQL (from DATABASE_URL)"
    echo "Running database migrations..."
    
    # Run Alembic migrations
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo "✓ Migrations completed successfully"
    else
        echo "⚠️ Warning: Migration failed, but continuing..."
    fi
else
    echo "Database: SQLite (${DB_PATH:-natal_nataly.sqlite})"
    echo "Skipping migrations for SQLite (tables will be created automatically)"
fi

echo ""
echo "Starting uvicorn server on port ${PORT:-8000}..."
echo ""

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
