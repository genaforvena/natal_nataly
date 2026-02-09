# natal_nataly

Stateful personal astrology assistant bot for Telegram with multi-profile support, natural language input, and conversational AI. Generates natal charts locally using Swiss Ephemeris and provides context-aware astrological guidance.

## Quick Start (One-Click Local Test)

### Option 1: Docker (Recommended - Works on Windows, macOS, Linux)

**Prerequisites:**
- Docker and Docker Compose installed ([Get Docker](https://docs.docker.com/get-docker/))

1. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/genaforvena/natal_nataly.git
   cd natal_nataly
   ```

2. **Create environment file `.env`:**
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key
   ```
   
   Get API keys from:
   - Telegram: https://t.me/botfather
   - Groq: https://console.groq.com
   - DeepSeek: https://platform.deepseek.com

3. **Start the bot with Docker Compose:**
   ```bash
   docker-compose up -d
   ```
   
   The server will start at http://localhost:8000

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the bot:**
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup (Linux/macOS)

1. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/genaforvena/natal_nataly.git
   cd natal_nataly
   ```

2. **Run the start script:**
   ```bash
   ./start.sh
   ```
   
   The script will:
   - Create a `.env` template if it doesn't exist
   - Guide you to add your API keys
   - Install dependencies automatically
   - Start the server at http://localhost:8000

3. **Configure your API keys:**
   
   Edit the `.env` file with your credentials:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key
   ```
   
   Get API keys from:
   - Telegram: https://t.me/botfather
   - Groq: https://console.groq.com
   - DeepSeek: https://platform.deepseek.com

4. **Set up Telegram webhook** (for production):
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
     -d "url=https://your-domain.com/webhook"
   ```

5. **Test locally with ngrok** (optional):
   ```bash
   ngrok http 8000
   # Use the ngrok URL to register webhook
   ```

## Features

- 🤖 **Conversational Assistant Mode** - Natural dialogue with persistent context
- 👥 **Multi-Profile Support** - Create profiles for yourself, partners, friends
- 🗣️ **Natural Language Input** - Describe birth data in any format or language
- 🧠 **Intent Classification** - Smart routing based on user's intent
- 💬 **Stateful Conversations** - Remembers your chart across sessions
- 📊 **Swiss Ephemeris** - Accurate astronomical calculations

## Architecture

```
Telegram Webhook
    ↓
Intent Classification (LLM)
    ↓
    ├─→ Birth Data Input → Chart Generation → Profile Creation
    ├─→ Profile Management → Switch/List Profiles
    ├─→ Chart Questions → Assistant Response (with context)
    └─→ General Questions → Astrology Knowledge Base
```

## Usage

### First Time Setup - Create Your Profile

Send birth data in **natural language** (any format works):
```
I was born on May 15, 1990 at 2:30 PM in New York

Born 1985-03-20, morning, Moscow

Родился 12 декабря 1992 года в 18:45 в Санкт-Петербурге
```

**Classic format also supported:**
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

The bot will ask for any missing information, then generate your natal chart.

### Conversational Mode

Once your chart is ready, just chat naturally:
```
"What are my natural talents?"
"Why do I struggle with relationships?"
"Tell me about my career potential"
"What does my Sun in Taurus mean?"
```

### Multi-Profile Management

**Create additional profiles:**
```
"Add my girlfriend Maria's profile"
[Bot asks for birth data]
```

**Switch between profiles:**
```
"Switch to Maria's profile"
```

**List all profiles:**
```
/profiles
```

The bot remembers your active profile and provides context-aware responses.

## Documentation

- See [DOCKER.md](DOCKER.md) for comprehensive Docker deployment guide
- See [SETUP.md](SETUP.md) for detailed manual setup instructions
- See [TEST_PAYLOADS.md](TEST_PAYLOADS.md) for testing examples
- See [STATEFUL_BOT_GUIDE.md](STATEFUL_BOT_GUIDE.md) for implementation details
- See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture overview
