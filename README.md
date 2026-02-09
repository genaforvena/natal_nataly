# natal_nataly

Telegram astrology bot that generates natal charts locally using Swiss Ephemeris
and produces AI-assisted readings.

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

## Pipeline

```
Telegram webhook → Validation → Natal chart → LLM interpretation → Reply
```

## Usage

Send a message to your bot in this format:
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

The bot will reply with a personalized astrological reading!

## Documentation

- See [DOCKER.md](DOCKER.md) for comprehensive Docker deployment guide
- See [SETUP.md](SETUP.md) for detailed manual setup instructions
- See [TEST_PAYLOADS.md](TEST_PAYLOADS.md) for testing examples
