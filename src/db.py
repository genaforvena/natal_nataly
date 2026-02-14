import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database URL configuration
# If DATABASE_URL exists → use it (PostgreSQL or other)
# If missing → check DB_PATH for legacy SQLite path, or use default
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_PATH = os.getenv("DB_PATH", "natal_nataly.sqlite")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Determine database backend for logging
db_backend = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
logger.info(f"Database backend: {db_backend}")
logger.info(f"Configuring database with URL: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL}")

# For PostgreSQL, use psycopg2; for SQLite, use default driver
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Verify connections before using them
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    logger.info("Initializing database schema")
    # Import models here to avoid circular import (models.py imports Base from this module)
    from src.models import (
        User, BirthData, Reading, AstroProfile, PipelineLog,
        NatalChart, DebugSession, UserNatalChart, ConversationMessage, ProcessedMessage
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully")
