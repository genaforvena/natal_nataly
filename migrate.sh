#!/bin/bash

# Database Migration Script for natal_nataly
# This script helps run Alembic migrations safely

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== natal_nataly Database Migration Tool ==="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with DATABASE_URL configured."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set in .env"
    echo "Will use SQLite fallback: natal_nataly.sqlite"
fi

echo "Database: ${DATABASE_URL:-SQLite (natal_nataly.sqlite)}"
echo ""

# Function to show current migration status
show_status() {
    echo "Current migration status:"
    alembic current || echo "No migrations applied yet"
    echo ""
    echo "Migration history:"
    alembic history
}

# Function to apply migrations
apply_migrations() {
    echo "Applying pending migrations..."
    alembic upgrade head
    echo ""
    echo "✓ Migrations applied successfully!"
    show_status
}

# Function to create new migration
create_migration() {
    read -p "Enter migration description: " desc
    if [ -z "$desc" ]; then
        echo "Error: Description cannot be empty"
        exit 1
    fi
    
    echo "Creating migration: $desc"
    alembic revision --autogenerate -m "$desc"
    echo ""
    echo "✓ Migration created!"
    echo "Review the generated file in alembic/versions/ before applying."
}

# Function to rollback migrations
rollback_migration() {
    read -p "How many migrations to rollback? (default: 1): " count
    count=${count:-1}
    
    echo "Rolling back $count migration(s)..."
    alembic downgrade -$count
    echo ""
    echo "✓ Rollback completed!"
    show_status
}

# Main menu
if [ "$#" -eq 0 ]; then
    echo "Usage:"
    echo "  ./migrate.sh status     - Show current migration status"
    echo "  ./migrate.sh upgrade    - Apply pending migrations"
    echo "  ./migrate.sh create     - Create a new migration"
    echo "  ./migrate.sh rollback   - Rollback migrations"
    echo ""
    exit 0
fi

case "$1" in
    status)
        show_status
        ;;
    upgrade|up)
        apply_migrations
        ;;
    create|new)
        create_migration
        ;;
    rollback|down)
        rollback_migration
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run ./migrate.sh with no arguments to see usage."
        exit 1
        ;;
esac
