# Telegram Astrology Bot Setup Guide

## Prerequisites

1. Python 3.12+
2. Telegram Bot Token from [@BotFather](https://t.me/botfather)
3. LLM API Key (DeepSeek or Groq)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create environment file `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# LLM Configuration (choose one)
LLM_PROVIDER=groq  # or "deepseek"

# If using Groq:
GROQ_API_KEY=your_groq_api_key_here

# If using DeepSeek:
# DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Secret token for Telegram webhook (recommended)
TELEGRAM_SECRET_TOKEN=your_secret_token_here
```

3. Create ephemeris directory (required for pyswisseph):
```bash
mkdir -p ephe
```

## Running the Bot

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

## Setting Up Telegram Webhook

After deploying your server to a public URL, register the webhook with Telegram, including your secret token for security:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook",
    "secret_token": "your_secret_token_here"
  }'
```

## Testing Locally

For local testing without deploying, you can use ngrok:

```bash
# Start ngrok
ngrok http 8000

# Use the ngrok URL to register webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-ngrok-url.ngrok.io/webhook",
    "secret_token": "your_secret_token_here"
  }'
```

## Using the Bot

Send a message to your bot with the following format:

```
DOB: YYYY-MM-DD
Time: HH:MM
Lat: xx.xxxx
Lng: xx.xxxx
```

### Example:
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

The bot will:
1. Parse and validate your birth data
2. Generate your natal chart using Swiss Ephemeris
3. Send the chart data to OpenAI for interpretation
4. Reply with a personalized astrological reading

## Input Format Requirements

- **DOB**: Date of birth in YYYY-MM-DD format
- **Time**: Birth time in 24-hour HH:MM format
- **Lat**: Latitude as a decimal number (positive for North, negative for South)
- **Lng**: Longitude as a decimal number (positive for East, negative for West)

All fields are required and case-insensitive.

## Finding Coordinates

You can find latitude and longitude coordinates using:
- [Google Maps](https://maps.google.com) - Right-click on a location
- [LatLong.net](https://www.latlong.net/)
- Any GPS app or service

## Error Messages

- **"Invalid format"**: Your message doesn't match the required format
- **"Failed to generate natal chart"**: There was an issue calculating your chart (check date/time validity)
- **"Unable to generate your astrological reading"**: The AI service is temporarily unavailable

## Health Check

Test if the server is running:
```bash
curl http://localhost:8000/health
```

Expected response: `{"status": "ok"}`

## Database

The bot stores:
- User information (telegram_id, first_seen, last_seen)
- Birth data records (telegram_id, dob, time, lat, lng, created_at)

Database file: `natal_nataly.sqlite` (created automatically)

## Troubleshooting

### ImportError for swisseph
Make sure pyswisseph is properly installed:
```bash
pip install --force-reinstall pyswisseph
```

### No ephemeris directory error
Create the ephe directory:
```bash
mkdir -p ephe
```

### LLM API errors
- Verify your API key is valid (GROQ_API_KEY or DEEPSEEK_API_KEY)
- Check your account has credits
- Ensure LLM_PROVIDER is set to "groq" or "deepseek"
- Verify the corresponding API key environment variable is set

### Telegram webhook not receiving messages
- Verify your server is publicly accessible
- Check the webhook is registered: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Ensure you're using HTTPS (required by Telegram)
