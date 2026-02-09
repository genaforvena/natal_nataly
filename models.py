from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Boolean
from datetime import datetime, timezone
from db import Base

# User state constants
STATE_AWAITING_BIRTH_DATA = "awaiting_birth_data"
STATE_AWAITING_CLARIFICATION = "awaiting_clarification"
STATE_HAS_CHART = "has_chart"
STATE_CHATTING_ABOUT_CHART = "chatting_about_chart"

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(String, primary_key=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    state = Column(String, default=STATE_AWAITING_BIRTH_DATA)  # Use state constants defined above
    natal_chart_json = Column(Text, nullable=True)  # Store generated natal chart
    missing_fields = Column(String, nullable=True)  # Comma-separated list of missing fields

class BirthData(Base):
    __tablename__ = "birth_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    dob = Column(String, nullable=False)
    time = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    birth_data_id = Column(Integer, nullable=True)  # Reference to BirthData if needed
    reading_text = Column(Text, nullable=False)
    delivered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)
