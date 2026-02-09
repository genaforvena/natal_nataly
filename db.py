import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use environment variable for database path, default to local
DB_PATH = os.getenv("DB_PATH", "natal_nataly.sqlite")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    from models import User, BirthData
    Base.metadata.create_all(bind=engine)
