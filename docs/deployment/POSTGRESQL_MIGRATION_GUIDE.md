# PostgreSQL Migration Guide

This guide explains how to use the new PostgreSQL support in natal_nataly.

## Overview

The natal_nataly bot now supports both SQLite (for local development) and PostgreSQL (for production deployment) with automatic detection based on environment variables.

## Database Configuration

### SQLite (Default - Local Development)

No configuration needed! The bot automatically uses SQLite if `DATABASE_URL` is not set.

```bash
# Simply run the bot - it will create natal_nataly.sqlite
python main.py
# or
docker-compose up
```

**File location:** `natal_nataly.sqlite` (or path specified in `DB_PATH`)

### PostgreSQL (Production - Render)

Set the `DATABASE_URL` environment variable to use PostgreSQL:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

The bot will automatically:
- Detect PostgreSQL from the connection string
- Enable connection pooling
- Create all tables on first startup
- Log the database backend being used

## Environment Variables

### DATABASE_URL
- **Purpose:** Specify database connection
- **Format:** 
  - PostgreSQL: `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`
  - SQLite: `sqlite:///path/to/file.db`
- **Default:** Falls back to SQLite if not set

### DB_PATH (Legacy)
- **Purpose:** SQLite database file path (used when DATABASE_URL not set)
- **Default:** `natal_nataly.sqlite`
- **Example:** `DB_PATH=data/natal_nataly.sqlite`

### PORT
- **Purpose:** Application port
- **Default:** `8000`
- **Render:** `10000`

### RENDER
- **Purpose:** Flag to enable Render-specific configuration
- **Values:** `true` or `false`
- **Default:** `false`

### WEBHOOK_URL
- **Purpose:** Telegram webhook URL (required when RENDER=true)
- **Example:** `https://your-app.onrender.com/webhook`

## Local Development

### Option 1: Direct Python
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (uses SQLite automatically)
python main.py
```

### Option 2: Docker Compose
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Production Deployment (Render)

### 1. Prepare Your Repository

Ensure these files are in your repository:
- `render.yaml` - Deployment configuration
- `Dockerfile` - Container definition
- `.env.example` - Environment variable template

### 2. Create Render Account

Go to [Render](https://render.com) and sign up.

### 3. Create PostgreSQL Database

1. Click **New +** → **PostgreSQL**
2. Name: `natal-nataly-db`
3. Plan: **Free**
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://`)

### 4. Create Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Select `natal_nataly` repository
4. Settings:
   - **Name:** `natal-nataly-bot`
   - **Environment:** Docker
   - **Plan:** Free
   - **Branch:** main

### 5. Configure Environment Variables

In the Web Service, add these environment variables:

```bash
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
LLM_PROVIDER=groq
GROQ_API_KEY=<your_groq_api_key>
DATABASE_URL=<internal_database_url_from_step_3>
RENDER=true
WEBHOOK_URL=https://your-app-name.onrender.com/webhook
PORT=10000
```

### 6. Deploy

Click **Create Web Service**. Render will:
1. Build your Docker image
2. Start the application
3. Connect to PostgreSQL
4. Create database tables automatically

### 7. Register Telegram Webhook

Once deployed, register your webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-name.onrender.com/webhook"}'
```

### 8. Verify Deployment

Check your Render service logs. You should see:

```
INFO:db:Database backend: postgresql
INFO:main:Running mode: render
INFO:main:Webhook enabled: True
INFO:db:Database schema initialized successfully
```

## Migrating Data

### From SQLite to PostgreSQL

There is no automatic migration. You have two options:

#### Option 1: Fresh Start (Recommended)
Simply deploy with PostgreSQL. Users will need to re-register their birth data.

#### Option 2: Manual Data Migration
1. Export data from SQLite:
   ```python
   import sqlite3
   import json
   
   conn = sqlite3.connect('natal_nataly.sqlite')
   cursor = conn.cursor()
   
   # Export users
   cursor.execute("SELECT * FROM users")
   users = cursor.fetchall()
   with open('users.json', 'w') as f:
       json.dump(users, f)
   
   # Export other tables similarly...
   ```

2. Import into PostgreSQL using SQLAlchemy scripts
3. Test thoroughly before switching production traffic

## Troubleshooting

### Issue: "No module named 'psycopg2'"
**Solution:** Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

### Issue: Database connection fails
**Solution:** Verify DATABASE_URL format:
- Must start with `postgresql://`
- Check username, password, host, port, database name
- Ensure PostgreSQL database exists and is running

### Issue: Tables not created
**Solution:** Check logs for errors. Tables are created automatically via:
```python
Base.metadata.create_all(bind=engine)
```

### Issue: Webhook not receiving messages
**Solutions:**
1. Verify WEBHOOK_URL is correct
2. Check Telegram webhook registration:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```
3. Ensure app is running and accessible
4. Check Render logs for errors

## Monitoring

### Check Database Backend
Look for this log line on startup:
```
INFO:db:Database backend: postgresql
```

### Check Database Connection
The app uses `pool_pre_ping=True` to verify connections before use.

### Health Check
```bash
curl https://your-app.onrender.com/health
# Should return: {"status": "ok"}
```

## Performance Tips

### PostgreSQL
- Connection pooling is enabled (pool_size=5, max_overflow=10)
- Connections are verified before use (pool_pre_ping=True)
- Free tier limits: 90 days of inactivity before deletion

### SQLite
- Single connection (no pooling)
- Suitable for local development
- Not recommended for production with multiple users

## Security Notes

1. **Never commit credentials:**
   - Use `.env` for local development
   - Use Render's environment variables for production

2. **Database URLs in logs:**
   - Credentials are hidden in logs (only host shown)

3. **Connection security:**
   - PostgreSQL connections use SSL by default on Render
   - SQLite is file-based (no network exposure)

## FAQ

**Q: Can I switch between SQLite and PostgreSQL?**
A: Yes, just change the `DATABASE_URL`. Tables will be created automatically.

**Q: Will my data be lost?**
A: Data is stored per database. Switching databases starts fresh unless you migrate data.

**Q: Can I use PostgreSQL locally?**
A: Yes! Install PostgreSQL locally and set `DATABASE_URL` appropriately.

**Q: What about database migrations?**
A: Currently using `create_all()`. For schema changes, consider adding Alembic in the future.

**Q: Is async supported?**
A: Currently using synchronous SQLAlchemy for minimal changes. Async could be added later.

## Support

For issues or questions:
1. Check Render logs
2. Check application logs
3. Review this guide
4. Open a GitHub issue

## Summary

✅ Zero-config local development (SQLite)
✅ Production-ready PostgreSQL support
✅ Automatic database detection
✅ One-click Render deployment
✅ Comprehensive logging
✅ Backward compatible
