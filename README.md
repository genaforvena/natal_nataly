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
   
   **Recommended:** For production security, set a secret token:
   ```bash
   # Generate a secure random token
   SECRET_TOKEN=$(openssl rand -hex 32)
   
   # Register webhook with secret token
   curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"https://your-domain.com/webhook\", \"secret_token\": \"$SECRET_TOKEN\"}"
   
   # Add the token to your .env file
   echo "TELEGRAM_SECRET_TOKEN=$SECRET_TOKEN" >> .env
   ```

5. **Test locally with ngrok** (optional):
   ```bash
   ngrok http 8000
   # Use the ngrok URL to register webhook
   ```

## Security Features

### Webhook Secret Token Verification

The bot supports Telegram's webhook secret token verification to prevent spoofed webhook requests:

- **Backward Compatible**: Works without the token for development
- **Production Ready**: Enable by setting `TELEGRAM_SECRET_TOKEN` environment variable
- **Automatic Verification**: Rejects unauthorized requests with invalid or missing tokens

To enable webhook security:
1. Generate a secure random token (32+ characters recommended)
2. Set `TELEGRAM_SECRET_TOKEN` in your `.env` file
3. Register the webhook with Telegram including the `secret_token` parameter
4. All webhook requests will be verified against the configured token

### Message Throttling

The bot implements intelligent message throttling to improve user experience:

- **15-Second Window**: Messages from the same user within 15 seconds are grouped
- **Automatic Merging**: Grouped messages are combined and processed together
- **Single Response**: The bot replies once for the entire message group
- **Per-User**: Throttling is applied independently for each user

This prevents response flooding when users send multiple quick messages and provides more coherent responses.

## Deploy to Render (Free Hosting)

natal_nataly can be deployed to [Render](https://render.com) with PostgreSQL support for production use.

### Deployment Steps

1. **Push your repository to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **New +** → **Web Service**
   - Connect your GitHub repository
   - Select `natal_nataly` repository

3. **Configure the service:**
   - **Name**: `natal-nataly-bot` (or your preferred name)
   - **Environment**: `Docker`
   - **Plan**: `Free`
   - **Branch**: `main`

4. **Add a PostgreSQL database:**
   - In Render Dashboard, click **New +** → **PostgreSQL**
   - **Name**: `natal-nataly-db`
   - **Plan**: `Free`
   - Click **Create Database**

5. **Configure Environment Variables:**
   
   In your Web Service settings, add these environment variables:
   
   ```bash
   TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
   TELEGRAM_SECRET_TOKEN=<generate_secure_random_token>
   LLM_PROVIDER=groq
   GROQ_API_KEY=<your_groq_api_key>
   DATABASE_URL=<copy_from_postgres_internal_database_url>
   RENDER=true
   WEBHOOK_URL=https://your-app-name.onrender.com/webhook
   PORT=10000
   ```
   
   **Important:** 
   - Copy `DATABASE_URL` from your PostgreSQL database's **Internal Database URL**
   - Replace `your-app-name` in `WEBHOOK_URL` with your actual Render service name
   - **Security**: Generate a secure random token for `TELEGRAM_SECRET_TOKEN` (e.g., `openssl rand -hex 32`)

6. **Deploy:**
   - Click **Create Web Service**
   - Render will automatically build and deploy your app
   - Wait for the deployment to complete (first build takes ~5 minutes)

7. **Register Telegram Webhook:**
   
   Once deployed, register your webhook with Telegram (with secret token for security):
   ```bash
   # Generate secret token (use the same value from TELEGRAM_SECRET_TOKEN env var)
   SECRET_TOKEN="your_secret_token_from_render_env"
   
   curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"https://your-app-name.onrender.com/webhook\", \"secret_token\": \"$SECRET_TOKEN\"}"
   ```

8. **Verify deployment:**
   - Check your service logs in Render Dashboard
   - Look for: `Database backend: postgresql` and `Running mode: render`
   - Send a test message to your Telegram bot

### Database Configuration

The bot automatically detects the database backend:
- **Local development**: Uses SQLite (`natal_nataly.sqlite`)
- **Production (Render)**: Uses PostgreSQL when `DATABASE_URL` is set

#### Database Migrations

The project uses Alembic for database schema migrations. When deploying or updating the application:

1. **Apply pending migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Check migration status:**
   ```bash
   alembic current
   ```

For more details, see [alembic/README_MIGRATIONS.md](alembic/README_MIGRATIONS.md).

**Important for Production:** Always run migrations before starting the application to ensure the database schema is up-to-date.

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

### User Data Transparency & Audit Commands

natal_nataly provides full transparency into your data and calculations:

**View your birth data:**
```
/my_data
```
Shows your complete birth data including:
- Date and time (local and UTC)
- Location coordinates
- Timezone information and source
- Natal chart status and engine version

**Access raw chart data:**
```
/my_chart_raw
```
Returns your natal chart in JSON format for verification on external services like AstroSeek.

**Review all your readings:**
```
/my_readings
```
Lists all your astrological readings with metadata (date, model used, prompt).

**Retrieve specific reading:**
```
/my_readings 5
```
Displays a specific reading by ID without regenerating it.

**Edit your birth data:**
```
/edit_birth
```
Allows you to update your birth data. Shows diff and requires confirmation.

**Data Confirmation Flow:**
When you first provide birth data, the bot will ask you to confirm before generating the chart:
- Shows all extracted data (date, time, location, timezone, coordinates)
- Reply **CONFIRM** to proceed
- Reply **EDIT** to modify the data

This prevents errors from incorrect timezone detection or coordinate rounding.

## Privacy & Security

- ✅ All users see only their own data
- ✅ Readings are stored in database for reuse (no redundant LLM calls)
- ✅ Birth data confirmation prevents incorrect chart generation
- ✅ Full audit trail of data sources (timezone, coordinates)
- ✅ Swiss Ephemeris version tracking for reproducibility

## Documentation

- See [docs/DOCKER_TESTING.md](docs/DOCKER_TESTING.md) for Docker deployment testing guide
- See [docs/guides/TESTING.md](docs/guides/TESTING.md) for CI/CD pipeline and testing guide
- See [docs/deployment/DOCKER.md](docs/deployment/DOCKER.md) for comprehensive Docker deployment guide
- See [docs/SETUP.md](docs/SETUP.md) for detailed manual setup instructions
- See [docs/TEST_PAYLOADS.md](docs/TEST_PAYLOADS.md) for testing examples
- See [docs/guides/STATEFUL_BOT_GUIDE.md](docs/guides/STATEFUL_BOT_GUIDE.md) for implementation details
- See [docs/guides/DEBUG_MODE.md](docs/guides/DEBUG_MODE.md) for debug mode and developer commands
- See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for project organization

## Debug Mode (Developer Tools)

natal_nataly includes a comprehensive debug mode for transparent inspection of all processing stages:

### Enable Debug Mode

Add to your `.env` file:
```bash
DEBUG_MODE=true
DEVELOPER_TELEGRAM_ID=your_telegram_id
```

### Developer Commands

- `/debug_birth` - Show parsed and normalized birth data
- `/debug_chart` - Show complete natal chart JSON with metadata
- `/debug_pipeline` - Show complete pipeline trace for latest session
- `/show_chart` - Generate and display SVG chart visualization

### Features

- **Pipeline Logging**: Tracks 5 stages from raw input to final reading
- **Natal Chart Storage**: Charts stored with versioning (Swiss Ephemeris version)
- **Timezone Validation**: Compares LLM-extracted timezone with geo lookup
- **LLM Prompt Tracking**: Stores prompt name, hash, and model for reproducibility
- **SVG Visualization**: Generates visual natal chart for verification

See [docs/guides/DEBUG_MODE.md](docs/guides/DEBUG_MODE.md) for complete documentation.
