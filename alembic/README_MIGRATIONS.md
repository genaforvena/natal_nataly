# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Prerequisites

Ensure Alembic is installed:
```bash
pip install alembic
```

## Running Migrations

### Apply Pending Migrations

To apply all pending migrations to your database:

```bash
# From the project root directory
alembic upgrade head
```

This will:
1. Connect to your database using the `DATABASE_URL` environment variable
2. Apply any pending migrations in order
3. Update the `alembic_version` table to track applied migrations

### Check Migration Status

To see which migrations have been applied:

```bash
alembic current
```

To see migration history:

```bash
alembic history --verbose
```

### Rollback Migrations

To rollback the last migration:

```bash
alembic downgrade -1
```

To rollback to a specific revision:

```bash
alembic downgrade <revision_id>
```

## Creating New Migrations

### Auto-generate Migration (Recommended)

When you make changes to models in `src/models.py`, you can auto-generate a migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

**Important**: Always review the generated migration before applying it!

### Manual Migration

To create an empty migration file:

```bash
alembic revision -m "Description of changes"
```

Then edit the generated file in `alembic/versions/` to add your migration logic.

## Environment Configuration

Migrations use the same database configuration as the main application:

- **DATABASE_URL** environment variable: PostgreSQL connection string
- If not set, falls back to SQLite at `natal_nataly.sqlite`

## Migration Files

Migration files are stored in `alembic/versions/` and follow the naming pattern:
```
<revision_id>_<description>.py
```

Each migration file contains:
- `upgrade()`: Function to apply the migration
- `downgrade()`: Function to revert the migration

## Example: Adding the user_profile Column

The first migration (`0e8cfa50b49c_add_user_profile_column_to_users_table.py`) adds the `user_profile` column to the `users` table. This fixes the production error where SQLAlchemy tried to query a column that didn't exist.

To apply this migration:
```bash
alembic upgrade head
```

## Troubleshooting

### "Can't locate revision identified by..."

This error means the `alembic_version` table in your database is out of sync. To reset:

```bash
# Stamp the database with the current revision (use with caution!)
alembic stamp head
```

### "Table already exists"

If Alembic tries to create a table that already exists, you may need to:
1. Skip that specific migration, or
2. Manually stamp the database to mark that migration as applied

### Production Deployment

For production deployments, run migrations as part of your deployment process:

```bash
# Before starting the application
alembic upgrade head

# Then start the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

In Docker, you can add this to your startup script or as a pre-start command.
