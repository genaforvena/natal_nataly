# Project Structure

This document describes the organization of the natal_nataly codebase.

## Directory Layout

```
natal_nataly/
├── src/                      # Application source code
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── bot.py               # Telegram bot logic and message handling
│   ├── astrology.py         # Natal chart generation (Swiss Ephemeris)
│   ├── llm.py               # LLM integration for AI interpretations
│   ├── db.py                # Database initialization and configuration
│   ├── models.py            # SQLAlchemy database models
│   ├── thread_manager.py    # Conversation thread management
│   ├── user_commands.py     # User command handlers (/my_data, etc.)
│   ├── chart_parser.py      # Chart data parsing and validation
│   ├── chart_svg.py         # SVG chart rendering
│   ├── prompt_loader.py     # LLM prompt template loader
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── chart_builder.py     # Natal chart text/JSON generation
│   │   ├── date_parser.py       # Date/time parsing utilities
│   │   ├── intent_router.py     # User intent classification
│   │   └── transit_builder.py   # Transit chart generation
│   └── prompts/             # LLM prompt templates
│       ├── personality.md
│       ├── parser/          # Parser prompts for birth data extraction
│       └── responses/       # Response generation prompts
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_bot.py          # Bot logic tests
│   ├── test_chart_builder.py   # Chart generation tests
│   ├── test_integration.py     # Integration tests
│   ├── test_llm.py             # LLM integration tests
│   └── test_thread_manager.py  # Thread management tests
│
├── scripts/                 # Utility scripts and debugging tools
│   ├── debug.py            # Debug mode implementation
│   ├── debug_commands.py   # Developer debug commands
│   └── demo_thread_management.py  # Demo script for thread feature
│
├── docs/                    # Documentation
│   ├── PROJECT_STRUCTURE.md    # This file
│   ├── SETUP.md                # Manual setup instructions
│   ├── TEST_PAYLOADS.md        # Example test messages
│   ├── THREAD_VISUALIZATION.txt # Thread management visualization
│   ├── deployment/             # Deployment guides
│   │   ├── DOCKER.md
│   │   └── POSTGRESQL_MIGRATION_GUIDE.md
│   ├── guides/                 # User and developer guides
│   │   ├── STATEFUL_BOT_GUIDE.md
│   │   ├── CONVERSATION_THREAD_GUIDE.md
│   │   ├── DEBUG_MODE.md
│   │   ├── UNIFIED_CHART_GUIDE.md
│   │   ├── TESTING.md
│   │   └── KERYKEION_MIGRATION.md
│   └── implementation/         # Implementation notes
│       ├── CI_CD_IMPLEMENTATION.md
│       ├── CI_CD_SUMMARY.md
│       ├── IMPLEMENTATION_DEBUG_MODE.md
│       ├── IMPLEMENTATION_PROMPT_ARCHITECTURE.md
│       ├── IMPLEMENTATION_SUMMARY_KERYKEION.md
│       ├── IMPLEMENTATION_SUMMARY_OLD.md
│       ├── IMPLEMENTATION_SUMMARY_THREAD_MANAGEMENT.md
│       ├── IMPLEMENTATION_SUMMARY_UNIFIED_CHART.md
│       ├── IMPLEMENTATION_TRANSIT_REQUESTS.md
│       └── IMPLEMENTATION_USER_TRANSPARENCY.md
│
├── .github/                 # GitHub configuration
├── .dockerignore            # Docker ignore file
├── .env.example             # Environment variables template
├── .flake8                  # Flake8 linter configuration
├── .gitignore              # Git ignore file
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── mypy.ini                # MyPy type checker configuration
├── pytest.ini              # Pytest configuration
├── README.md               # Main project README
├── render.yaml             # Render.com deployment config
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
└── start.sh                # Quick start script
```

## Module Responsibilities

### Core Application (`src/`)

- **main.py** - FastAPI application with webhook and health check endpoints
- **bot.py** - Main bot logic: message parsing, state management, response generation
- **astrology.py** - Wraps Swiss Ephemeris for natal chart calculations
- **llm.py** - OpenAI-compatible API integration (Groq, DeepSeek)
- **db.py** - Database engine and session management (SQLite/PostgreSQL)
- **models.py** - SQLAlchemy ORM models for User, BirthData, Reading, etc.

### Services (`src/services/`)

Business logic extracted into reusable services:

- **chart_builder.py** - Generates natal chart text representations and JSON
- **date_parser.py** - Parses natural language date/time input
- **intent_router.py** - Classifies user intent for request routing
- **transit_builder.py** - Generates transit charts

### Scripts (`scripts/`)

Utilities and debugging tools (not part of main application):

- **debug.py** - Debug mode features and pipeline logging
- **debug_commands.py** - Developer-only debug commands
- **demo_thread_management.py** - Demonstration of thread management feature

### Tests (`tests/`)

Pytest-based test suite following standard Python conventions:

- Unit tests for individual modules
- Integration tests for API interactions
- All tests use `pytest` and standard testing practices

### Documentation (`docs/`)

All project documentation organized by category:

- **deployment/** - Deployment and infrastructure guides
- **guides/** - Feature guides and user documentation
- **implementation/** - Technical implementation notes and decisions

## Import Structure

All imports use the `src.` prefix for application code:

```python
# In application code (src/)
from src.bot import handle_telegram_update
from src.db import SessionLocal
from src.models import User, BirthData

# In tests/
from src.bot import split_message
from src.llm import call_llm

# In scripts/
from src.db import SessionLocal, init_db
from scripts.debug import is_developer
```

## Running the Application

### Local Development

```bash
# With start.sh (sets up PYTHONPATH automatically)
./start.sh

# Manual
export PYTHONPATH="$PYTHONPATH:$(pwd)"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
# Dockerfile automatically sets PYTHONPATH=/app
docker-compose up -d
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_bot.py

# With coverage
pytest --cov=src tests/
```

## Configuration Files

- **pytest.ini** - Pytest configuration, test markers, and paths
- **mypy.ini** - Type checking configuration
- **.flake8** - Code style linting rules
- **requirements.txt** - Production dependencies
- **requirements-dev.txt** - Development tools (pytest, flake8, mypy)
- **.env.example** - Template for environment variables

## Environment Variables

All configuration via environment variables (see `.env.example`):

- `TELEGRAM_BOT_TOKEN` - Telegram Bot API token
- `LLM_PROVIDER` - AI provider (groq/deepseek)
- `GROQ_API_KEY` / `DEEPSEEK_API_KEY` - API keys
- `DATABASE_URL` - Database connection string (optional, defaults to SQLite)
- `DEBUG_MODE` - Enable debug features (optional)
- `DEVELOPER_TELEGRAM_ID` - Developer Telegram ID for debug commands (optional)

## Database Files

- **natal_nataly.sqlite** - SQLite database (local development, created automatically)
- **data/** - Docker volume for persistent data

## Build Artifacts

Not committed to git (see `.gitignore`):

- `__pycache__/` - Python bytecode
- `*.pyc`, `*.pyo` - Compiled Python files
- `.pytest_cache/` - Pytest cache
- `.mypy_cache/` - MyPy cache
- `ephe/` - Swiss Ephemeris data directory (created at runtime)
