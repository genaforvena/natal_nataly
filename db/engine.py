"""Database engine configuration with async PostgreSQL/SQLite support"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# Database URL configuration
# If DATABASE_URL exists → use it (PostgreSQL or other)
# If missing → fallback to SQLite with aiosqlite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///natal_nataly.sqlite"
)

# Determine database backend for logging
db_backend = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
logger.info(f"Database backend: {db_backend}")
logger.info(f"Database URL configured: {DATABASE_URL.split('@')[0]}...")  # Hide credentials

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
    # For PostgreSQL, add connection pool settings
    pool_size=5 if "postgresql" in DATABASE_URL else 0,
    max_overflow=10 if "postgresql" in DATABASE_URL else 0,
)

# Declarative base for models
Base = declarative_base()

async def init_db():
    """Initialize database schema (create tables if they don't exist)"""
    logger.info("Initializing database schema")
    
    # Import models to ensure they're registered with Base
    from .models import (
        User, BirthData, Reading, AstroProfile, 
        PipelineLog, NatalChart, DebugSession, UserNatalChart
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database schema initialized successfully")
