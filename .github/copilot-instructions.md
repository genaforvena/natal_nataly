# Copilot Instructions for natal_nataly

## Project Overview

natal_nataly is a Telegram astrology bot that generates natal charts locally using Swiss Ephemeris and produces AI-assisted astrological readings. The bot is built with Python using FastAPI and runs as a webhook-based service that integrates with Telegram's Bot API.

**Tech Stack:**
- **Language**: Python 3.12+
- **Web Framework**: FastAPI with uvicorn
- **Telegram Integration**: python-telegram-bot (via direct HTTP API calls with httpx)
- **Astrology Engine**: pyswisseph (Swiss Ephemeris)
- **Database**: SQLite via SQLAlchemy
- **LLM Integration**: OpenAI SDK (supports Groq and DeepSeek providers)
- **Deployment**: Docker and Docker Compose

## Build and Run Instructions

### Quick Start (Recommended)

**Using Docker (Works on all platforms):**
```bash
# 1. Create .env file with credentials:
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN, LLM_PROVIDER, and API keys

# 2. Start the bot:
docker-compose up -d

# 3. View logs:
docker-compose logs -f

# 4. Stop the bot:
docker-compose down
```

**Using Manual Setup (Linux/macOS):**
```bash
# 1. Run the automated start script:
./start.sh
# The script will create .env template, install dependencies, and start the server

# 2. Configure .env file with your credentials when prompted

# 3. Run ./start.sh again to start the bot
```

### Manual Setup Steps

**Prerequisites:**
- Python 3.12+ installed
- pip package manager

**Step-by-step:**
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create ephemeris directory** (REQUIRED for pyswisseph):
   ```bash
   mkdir -p ephe
   ```
   Note: This directory is required by pyswisseph to store ephemeris data. The bot will fail if this directory doesn't exist.

3. **Configure environment variables** - Create `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   LLM_PROVIDER=groq  # or "deepseek"
   GROQ_API_KEY=your_groq_api_key_here
   # DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```
   
   Get API keys from:
   - Telegram: https://t.me/botfather
   - Groq: https://console.groq.com
   - DeepSeek: https://platform.deepseek.com

4. **Start the server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Server runs at: http://localhost:8000

5. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response: `{"status": "ok"}`

### Setting Up Telegram Webhook

For production deployment:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/webhook"}'
```

For local testing with ngrok:
```bash
ngrok http 8000
# Use the ngrok HTTPS URL to register webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ngrok-url.ngrok.io/webhook"}'
```

## Testing

**No formal test suite exists.** The bot is tested manually by:

1. Starting the server (locally or via Docker)
2. Sending test messages to the Telegram bot
3. Verifying responses

**Test message format:**
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

See `TEST_PAYLOADS.md` for more example test inputs.

## Project Structure

### Root Files
- **`main.py`** - FastAPI application entry point with `/webhook` and `/health` endpoints
- **`bot.py`** - Telegram bot logic: message parsing, validation, and response handling
- **`astrology.py`** - Natal chart generation using pyswisseph
- **`llm.py`** - LLM integration for astrological interpretations (supports Groq and DeepSeek)
- **`db.py`** - Database initialization and session management
- **`models.py`** - SQLAlchemy models: User and BirthData
- **`start.sh`** - Automated setup and startup script for manual deployment
- **`requirements.txt`** - Python dependencies
- **`.env.example`** - Template for environment variables
- **`docker-compose.yml`** - Docker Compose configuration for containerized deployment
- **`Dockerfile`** - Docker image definition

### Documentation
- **`README.md`** - Quick start guide and usage instructions
- **`SETUP.md`** - Detailed manual setup instructions
- **`DOCKER.md`** - Comprehensive Docker deployment guide
- **`TEST_PAYLOADS.md`** - Example test messages for bot testing

### Key Directories
- **`ephe/`** - Ephemeris data directory (created at runtime, required by pyswisseph)
- **Database file**: `natal_nataly.sqlite` (created automatically on first run)

## Development Workflow

### Making Code Changes

1. **Understand the request flow:**
   - Telegram sends webhook POST to `/webhook` endpoint (main.py)
   - Bot parses message and extracts birth data (bot.py)
   - Natal chart is generated using Swiss Ephemeris (astrology.py)
   - LLM interprets the chart and generates reading (llm.py)
   - Response is sent back to user via Telegram API (bot.py)

2. **Common modification areas:**
   - **Message parsing**: Edit `bot.py` - `parse_birth_data()` function
   - **Chart generation**: Edit `astrology.py` - `generate_natal_chart()` function
   - **LLM prompts**: Edit `llm.py` - `interpret_chart()` function
   - **Database models**: Edit `models.py` and run database migrations if needed

3. **Testing changes:**
   - Start the server: `uvicorn main:app --reload` (auto-reloads on file changes)
   - Send test messages through Telegram bot
   - Check logs for errors (logging configured in main.py and individual modules)

### Environment Variables

All sensitive configuration is stored in `.env` file (never commit this):
- `TELEGRAM_BOT_TOKEN` - Required for Telegram API
- `LLM_PROVIDER` - Must be "groq" or "deepseek"
- `GROQ_API_KEY` - Required if LLM_PROVIDER=groq
- `DEEPSEEK_API_KEY` - Required if LLM_PROVIDER=deepseek

### Common Issues and Solutions

1. **ImportError for swisseph**: Run `pip install --force-reinstall pyswisseph`
2. **No ephemeris directory error**: Create directory with `mkdir -p ephe`
3. **LLM API errors**: Verify API key is valid and account has credits
4. **Webhook not receiving messages**: 
   - Verify server is publicly accessible
   - Check webhook registration: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
   - Ensure using HTTPS (required by Telegram)

### Logging

Logging is configured in `main.py`:
- Log level: INFO by default
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- httpx and httpcore logs are set to WARNING to reduce noise
- Each module has its own logger instance

### Database

- **Engine**: SQLite (file: `natal_nataly.sqlite`)
- **Models**: User, BirthData (defined in models.py)
- **Initialization**: Automatic on startup via `init_db()` in main.py
- No migrations system - tables are created using SQLAlchemy's `create_all()`

## Important Notes for Copilot

1. **Always create the `ephe/` directory** when setting up the project - it's required by pyswisseph
2. **Never commit `.env` files** - they contain sensitive API keys
3. **Telegram requires HTTPS** for webhooks in production (use ngrok for local testing)
4. **The bot uses direct HTTP API calls** to Telegram (via httpx) rather than python-telegram-bot's higher-level abstractions
5. **No CI/CD pipeline exists** - validation is manual through testing
6. **No linting or formatting tools** are configured
7. **Docker is the recommended deployment method** - it handles all dependencies and environment setup
8. **LLM provider can be switched** by changing `LLM_PROVIDER` environment variable (groq or deepseek)
9. **Input format is strict** - users must provide DOB, Time, Lat, Lng in exact format or bot returns error message
