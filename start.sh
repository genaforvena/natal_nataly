#!/bin/bash
set -e

echo "=========================================="
echo "  Natal Nataly - Telegram Astrology Bot"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << 'EOF'
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# LLM Provider Configuration
# Options: "groq" or "deepseek"
LLM_PROVIDER=groq

# Groq API Key (if using Groq)
GROQ_API_KEY=your_groq_api_key_here

# DeepSeek API Key (if using DeepSeek)
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
EOF
    echo "✓ Created .env template"
    echo ""
    echo "❌ Please edit .env file with your actual API keys:"
    echo "   1. Get Telegram token from https://t.me/botfather"
    echo "   2. Get Groq API key from https://console.groq.com"
    echo "   3. Or get DeepSeek API key from https://platform.deepseek.com"
    echo ""
    echo "Then run ./start.sh again"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env file"
    exit 1
fi

if [ "$LLM_PROVIDER" = "groq" ]; then
    if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
        echo "❌ GROQ_API_KEY not set in .env file"
        exit 1
    fi
elif [ "$LLM_PROVIDER" = "deepseek" ]; then
    if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
        echo "❌ DEEPSEEK_API_KEY not set in .env file"
        exit 1
    fi
else
    echo "❌ LLM_PROVIDER must be 'groq' or 'deepseek'"
    exit 1
fi

echo ""
echo "✓ Environment variables loaded"

# Create ephemeris directory if it doesn't exist
if [ ! -d ephe ]; then
    echo "✓ Creating ephemeris directory..."
    mkdir -p ephe
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo ""
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

echo ""
echo "🚀 Starting Natal Nataly bot..."
echo ""
echo "Server will be available at: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Add src to PYTHONPATH for correct imports
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Start the server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
