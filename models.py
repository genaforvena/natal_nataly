from sqlalchemy import Column, String, DateTime, Integer, Float
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(String, primary_key=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class BirthData(Base):
    __tablename__ = "birth_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    dob = Column(String, nullable=False)
    time = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
