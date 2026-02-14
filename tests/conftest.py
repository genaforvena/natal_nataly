"""
Pytest configuration and fixtures for all tests.

Sets up environment variables and common test fixtures.
"""

import os
import pytest
import tempfile

# Create a temporary database file for tests (shared across all test sessions)
test_db_path = os.path.join(tempfile.gettempdir(), "test_natal_nataly.db")

# Set up minimal environment variables for testing
# These are required for the src modules to import properly
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_bot_token_12345")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test_groq_api_key_12345")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{test_db_path}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize database tables for testing."""
    from src.db import init_db, engine
    from src.models import Base
    
    # Remove old test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Initialize database tables
    init_db()
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)
    # Remove test database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope="session")
def test_environment():
    """Ensure test environment variables are set."""
    return {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN"),
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER"),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY"),
    }

