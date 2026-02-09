import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Use environment variable for database path, default to local
DB_PATH = os.getenv("DB_PATH", "natal_nataly.sqlite")
DATABASE_URL = f"sqlite:///{DB_PATH}"

logger.info(f"Configuring database with URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    logger.info("Initializing database schema")
    from models import User, BirthData, Reading
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully")
