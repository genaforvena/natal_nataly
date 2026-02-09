# Docker Deployment Guide

This guide explains how to run the Natal Nataly bot using Docker on any platform (Windows, macOS, Linux).

## Prerequisites

- **Docker** and **Docker Compose** installed on your system
  - [Get Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Get Docker Desktop for macOS](https://docs.docker.com/desktop/install/mac-install/)
  - [Get Docker Engine for Linux](https://docs.docker.com/engine/install/)

## Quick Start with Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/genaforvena/natal_nataly.git
cd natal_nataly
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
```

**Get API Keys:**
- Telegram Bot Token: https://t.me/botfather
- Groq API Key: https://console.groq.com
- DeepSeek API Key (alternative): https://platform.deepseek.com

### 3. Start the Bot

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the container in detached mode
- Expose port 8000 on your host machine
- Persist the SQLite database in the `./data` directory

### 4. Verify the Bot is Running

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"ok"}`

View logs:
```bash
docker-compose logs -f
```

### 5. Set Up Telegram Webhook

After the bot is running and accessible via a public URL, register the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook"
```

### 6. Stop the Bot

```bash
docker-compose down
```

## Manual Docker Commands

If you prefer not to use Docker Compose:

### Build the Image

```bash
docker build -t natal-nataly .
```

### Run the Container

```bash
docker run -d \
  --name natal-nataly-bot \
  -p 8000:8000 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  natal-nataly
```

### View Logs

```bash
docker logs -f natal-nataly-bot
```

### Stop the Container

```bash
docker stop natal-nataly-bot
docker rm natal-nataly-bot
```

## Docker Compose Commands Reference

| Command | Description |
|---------|-------------|
| `docker-compose up` | Start the bot in foreground |
| `docker-compose up -d` | Start the bot in background (detached) |
| `docker-compose down` | Stop and remove containers |
| `docker-compose logs` | View logs |
| `docker-compose logs -f` | Follow logs in real-time |
| `docker-compose ps` | List running containers |
| `docker-compose restart` | Restart the bot |
| `docker-compose build` | Rebuild the image |
| `docker-compose up -d --build` | Rebuild and restart |

## Data Persistence

The bot uses a SQLite database that is persisted in the `./data` directory on your host machine. This means:

- Your data survives container restarts
- You can backup the `./data` directory
- The database is stored outside the container

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Your Telegram bot token from BotFather |
| `LLM_PROVIDER` | Yes | `groq` | LLM provider: `groq` or `deepseek` |
| `GROQ_API_KEY` | If using Groq | - | Groq API key |
| `DEEPSEEK_API_KEY` | If using DeepSeek | - | DeepSeek API key |
| `DB_PATH` | No | `/app/data/natal_nataly.sqlite` | Database file path |

## Port Configuration

By default, the bot runs on port 8000. To change this, edit `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"  # Maps host port 9000 to container port 8000
```

## Troubleshooting

### Container Won't Start

1. Check logs: `docker-compose logs`
2. Verify environment variables in `.env` file
3. Ensure ports are not already in use: `docker ps`

### Database Issues

1. Check permissions on `./data` directory
2. Verify the directory exists: `mkdir -p data`
3. Check database file: `ls -la data/`

### Health Check Failing

1. Wait 10-30 seconds after starting (initial startup time)
2. Check if the container is running: `docker-compose ps`
3. Verify the application logs: `docker-compose logs`

### Can't Access from Outside

1. For production, you need a public domain/IP
2. Use a reverse proxy (nginx, Caddy) for HTTPS
3. For local testing, use ngrok or similar tunneling service

## Production Deployment

### Using a Reverse Proxy

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using Docker Compose with SSL

You can extend `docker-compose.yml` to include a reverse proxy with SSL:

```yaml
version: '3.8'

services:
  natal-nataly:
    build: .
    expose:
      - "8000"
    # ... rest of configuration

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - natal-nataly
```

## Updating the Bot

To update to the latest version:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

## Backup and Restore

### Backup

```bash
# Backup database
cp -r data/ backup-$(date +%Y%m%d)/

# Or create a tar archive
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Restore

```bash
# Restore from directory
cp -r backup-20260209/data/ ./data/

# Or extract from archive
tar -xzf backup-20260209.tar.gz
```

## Security Notes

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Use HTTPS in production** - Telegram requires HTTPS for webhooks
3. **Keep Docker images updated** - Rebuild periodically for security patches
4. **Restrict network access** - Use firewalls to limit who can access port 8000
5. **Backup regularly** - Protect your user data

## Platform-Specific Notes

### Windows

- Use PowerShell or Command Prompt
- Paths in volumes use forward slashes: `./data:/app/data`
- Docker Desktop must be running

### macOS

- Docker Desktop must be running
- File sharing must be enabled for the project directory
- Use Terminal or iTerm2

### Linux

- Native Docker support
- May need to use `sudo` for Docker commands (or add user to docker group)
- Better performance than Docker Desktop on other platforms
