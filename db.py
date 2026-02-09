from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

# Configure logging
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///natal_nataly.sqlite"

logger.info(f"Configuring database with URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    logger.info("Initializing database schema")
    from models import User, BirthData
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully")
