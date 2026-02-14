"""
Pytest configuration and fixtures for all tests.

Sets up environment variables and common test fixtures.
"""

import os
import pytest

# Set up minimal environment variables for testing
# These are required for the src modules to import properly
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_bot_token_12345")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test_groq_api_key_12345")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize database tables for testing."""
    from src.db import init_db
    init_db()
    yield


@pytest.fixture(scope="session")
def test_environment():
    """Ensure test environment variables are set."""
    return {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN"),
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER"),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY"),
    }
