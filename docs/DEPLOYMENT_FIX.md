# Deployment Guide: Fixing the user_profile Column Error

## Problem

The production database is missing the `user_profile` column in the `users` table, causing this error:

```
psycopg2.errors.UndefinedColumn: column users.user_profile does not exist
```

## Solution

We've added a database migration system using Alembic that will automatically add the missing column.

## Deployment Steps

### Option 1: Automatic Migration (Recommended for Docker/Render)

If you're using the Docker deployment, the migration will run automatically when the container starts.

1. **Push the changes to your repository:**
   ```bash
   git pull origin main
   ```

2. **Redeploy your application:**
   - **For Render:** Trigger a manual deploy or push to your branch
   - **For Docker:** Rebuild and restart the container:
     ```bash
     docker-compose down
     docker-compose build
     docker-compose up -d
     ```

3. **Verify the migration:**
   Check the logs to confirm the migration ran:
   ```bash
   # For Docker:
   docker-compose logs | grep migration
   
   # For Render:
   Check the deployment logs in the Render dashboard
   ```
   
   You should see:
   ```
   Running database migrations...
   ✓ Migrations completed successfully
   ```

### Option 2: Manual Migration (For Direct Server Access)

If you have direct access to the production server:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your DATABASE_URL:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   ```

3. **Run the migration:**
   ```bash
   alembic upgrade head
   ```

4. **Verify the migration:**
   ```bash
   alembic current
   ```
   
   You should see:
   ```
   0e8cfa50b49c (head)
   ```

5. **Start the application:**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

### Option 3: Using the Migration Helper Script

1. **Make the script executable:**
   ```bash
   chmod +x migrate.sh
   ```

2. **Run the migration:**
   ```bash
   ./migrate.sh upgrade
   ```

## Verification

After deployment, verify the fix by:

1. **Check the database schema:**
   ```sql
   \d users  -- In psql
   ```
   
   You should see the `user_profile` column listed.

2. **Test the bot:**
   Send a message to your bot. The error should no longer occur.

3. **Check application logs:**
   The `user_profile` error should no longer appear in the logs.

## What This Migration Does

The migration adds a new column to the `users` table:

```sql
ALTER TABLE users ADD COLUMN user_profile TEXT NULL;
```

This column is used for storing dynamic user profile information that helps personalize bot responses. It's nullable, so existing users won't be affected.

## Rollback (If Needed)

If you need to rollback the migration:

```bash
alembic downgrade -1
```

This will remove the `user_profile` column. However, this is **not recommended** as it will break the user profile functionality.

## Troubleshooting

### Error: "relation 'alembic_version' does not exist"

This means Alembic hasn't been initialized in your database yet. This is expected for first-time migration. The migration will create this table automatically.

### Error: "column users.user_profile already exists"

This means the migration has already been applied. You can verify with:

```bash
alembic current
```

If it shows the revision `0e8cfa50b49c`, the migration is already applied.

### Error: "Can't locate revision identified by..."

Your database's migration state is out of sync. To fix:

```bash
# Check current state
alembic current

# If no revision is shown, manually stamp the database
alembic stamp 0e8cfa50b49c
```

## For Future Migrations

Whenever you update the application and new migrations are added:

1. **Docker users:** Just rebuild and restart the container
2. **Manual deployment:** Run `alembic upgrade head` before starting the app
3. **Render users:** Redeploy, and migrations will run automatically

Always check the `alembic/versions/` directory for new migration files after pulling updates.
