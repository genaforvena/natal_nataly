# Database Migration Fix - Summary

## Problem Fixed

**Error**: `psycopg2.errors.UndefinedColumn: column users.user_profile does not exist`

**Root Cause**: The `User` model in `src/models.py` was updated to include a `user_profile` column for dynamic user profiling, but the production PostgreSQL database wasn't migrated. The `init_db()` function uses SQLAlchemy's `create_all()` which only creates new tables, not new columns in existing tables.

## Solution Implemented

Added Alembic database migration system to manage schema changes across all deployments.

## Files Added/Modified

### New Files
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Alembic environment setup (configured to use project's database)
- `alembic/versions/0e8cfa50b49c_add_user_profile_column_to_users_table.py` - Migration script
- `alembic/README_MIGRATIONS.md` - Migration system documentation
- `docker-entrypoint.sh` - Startup script that runs migrations automatically
- `migrate.sh` - Local migration helper script
- `docs/DEPLOYMENT_FIX.md` - Deployment guide

### Modified Files
- `requirements.txt` - Added `alembic` dependency
- `Dockerfile` - Updated to copy Alembic files and use entrypoint script
- `README.md` - Added database migration section
- `.dockerignore` - Updated to include `alembic/README_MIGRATIONS.md`

## What the Migration Does

Adds the missing `user_profile` column to the `users` table:

```sql
ALTER TABLE users ADD COLUMN user_profile TEXT NULL;
```

The column is nullable, so existing users are not affected.

## Deployment Instructions

### For Docker/Render (Automatic)

1. **Pull/deploy the latest code** - The migration will run automatically when the container starts
2. **Check logs** to confirm:
   ```
   Running database migrations...
   ✓ Migrations completed successfully
   ```

### For Manual Deployment

1. **Backup your database** (recommended)
2. **Set DATABASE_URL** environment variable
3. **Run migration**:
   ```bash
   alembic upgrade head
   ```
4. **Verify**:
   ```bash
   alembic current
   # Should show: 0e8cfa50b49c (head)
   ```
5. **Start the application**

### For Local Development

Use the helper script:
```bash
./migrate.sh upgrade
```

## Testing Verification

- ✅ All 14 user profile manager tests pass
- ✅ Migration tested on SQLite database
- ✅ Simulated production error and verified fix
- ✅ Docker entrypoint logic tested
- ✅ CodeQL security scan passed (no vulnerabilities)

## Backwards Compatibility

- ✅ Column is nullable - existing users unaffected
- ✅ SQLite databases skip migrations (tables created fresh)
- ✅ Existing functionality continues to work
- ✅ Migration is idempotent (safe to run multiple times)

## Rollback (If Needed)

If you need to rollback:

```bash
alembic downgrade -1
```

This will remove the `user_profile` column. However, this is **not recommended** as it will break the user profile feature.

## Future Migrations

Whenever schema changes are made:

1. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Review the generated migration** in `alembic/versions/`

3. **Test locally**:
   ```bash
   alembic upgrade head
   ```

4. **Commit and deploy** - migrations run automatically in Docker

## Support

For issues or questions:
- See `alembic/README_MIGRATIONS.md` for detailed migration usage
- See `docs/DEPLOYMENT_FIX.md` for deployment troubleshooting
- Check logs for error messages during migration

## Technical Details

- **Migration Framework**: Alembic 1.18.4
- **Migration ID**: 0e8cfa50b49c
- **Database Support**: PostgreSQL (production), SQLite (development)
- **Automatic Execution**: Yes (via docker-entrypoint.sh)
- **Rollback Support**: Yes (via `alembic downgrade`)
