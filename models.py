from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Boolean, ForeignKey
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
    natal_chart_json = Column(Text, nullable=True)  # Store generated natal chart (legacy, use AstroProfile instead)
    missing_fields = Column(String, nullable=True)  # Comma-separated list of missing fields
    active_profile_id = Column(Integer, ForeignKey('astro_profiles.id'), nullable=True)  # Reference to active AstroProfile
    assistant_mode = Column(Boolean, default=True)  # Enable assistant-style conversation mode

class AstroProfile(Base):
    """
    Represents an astrology profile (self, partner, friend, etc.)
    One user can have multiple profiles
    """
    __tablename__ = "astro_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)  # FK to User
    name = Column(String, nullable=True)  # Optional name (e.g., "Maria", "Alex", or None for "self")
    profile_type = Column(String, default="self")  # self|partner|friend|analysis
    birth_data_json = Column(Text, nullable=False)  # JSON: {dob, time, lat, lng}
    natal_chart_json = Column(Text, nullable=True)  # JSON: generated natal chart
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
