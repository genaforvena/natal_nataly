from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Boolean, ForeignKey
from datetime import datetime, timezone
from src.db import Base

# User state constants
STATE_AWAITING_BIRTH_DATA = "awaiting_birth_data"
STATE_AWAITING_CLARIFICATION = "awaiting_clarification"
STATE_AWAITING_CONFIRMATION = "awaiting_confirmation"
STATE_AWAITING_EDIT_CONFIRMATION = "awaiting_edit_confirmation"
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
    pending_birth_data = Column(Text, nullable=True)  # JSON: birth data pending confirmation
    pending_normalized_data = Column(Text, nullable=True)  # JSON: normalized birth data pending confirmation
    user_profile = Column(Text, nullable=True)  # Dynamic user profile document (LLM-maintained, max ~4000 chars)

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
    # LLM prompt tracking for reproducibility
    prompt_name = Column(String, nullable=True)  # Name of prompt template used
    prompt_hash = Column(String, nullable=True)  # Hash of prompt content for versioning
    model_used = Column(String, nullable=True)  # LLM model identifier


# ============================================================================
# DEBUG MODE MODELS - Debuggable Nataly
# ============================================================================

class PipelineLog(Base):
    """
    Stores debug information for each stage of the pipeline.
    Enables full trace of raw input → parsed data → normalized data → chart → reading.
    """
    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    session_id = Column(String, nullable=False)  # Not unique - multiple log entries per session across stages
    
    # Stage 1: Raw Input
    raw_user_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Stage 2: Parsed Birth Data (LLM output)
    parsed_birth_data_json = Column(Text, nullable=True)  # Complete LLM response
    
    # Stage 3: Normalized Birth Data
    normalized_birth_data_json = Column(Text, nullable=True)  # After system validation
    birth_datetime_utc = Column(DateTime, nullable=True)
    birth_datetime_local = Column(DateTime, nullable=True)
    timezone = Column(String, nullable=True)
    timezone_source = Column(String, nullable=True)  # api|fallback|manual
    timezone_validation_status = Column(String, nullable=True)  # MATCH|MISMATCH
    coordinates_source = Column(String, nullable=True)
    
    # Stage 4: Astrology Engine Output
    natal_chart_id = Column(Integer, ForeignKey('natal_charts.id'), nullable=True)
    
    # Pipeline status
    stage_completed = Column(String, nullable=True)  # raw_input|parsed|normalized|chart_generated|reading_sent
    error_message = Column(Text, nullable=True)


class NatalChart(Base):
    """
    Stores complete natal chart data with versioning.
    Source of truth for all astrological calculations.
    """
    __tablename__ = "natal_charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    
    # Complete chart data
    birth_data_json = Column(Text, nullable=False)  # DOB, time, lat, lng
    natal_chart_json = Column(Text, nullable=False)  # Complete chart: planets, houses, aspects, angles
    
    # Versioning for reproducibility
    engine_version = Column(String, nullable=True)  # pyswisseph version
    ephemeris_version = Column(String, nullable=True)  # Swiss Ephemeris data version
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    chart_hash = Column(String, nullable=True)  # Hash of chart for quick comparison
    
    # Additional raw ephemeris data for advanced debugging
    raw_ephemeris_data = Column(Text, nullable=True)


class DebugSession(Base):
    """
    Tracks complete debug sessions for developer analysis.
    Links all pipeline stages together for easy reproduction.
    """
    __tablename__ = "debug_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, unique=True, nullable=False)
    telegram_id = Column(String, nullable=False)
    
    # Pipeline references
    pipeline_log_id = Column(Integer, ForeignKey('pipeline_logs.id'), nullable=True)
    natal_chart_id = Column(Integer, ForeignKey('natal_charts.id'), nullable=True)
    reading_id = Column(Integer, ForeignKey('readings.id'), nullable=True)
    
    # Session metadata
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)  # in_progress|completed|failed


class UserNatalChart(Base):
    """
    Unified natal chart storage - single source of truth for all chart data.
    Supports both generated and user-uploaded charts in standardized JSON format.
    """
    __tablename__ = "user_natal_charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    
    # Standardized chart data in JSON format
    # Contains: planets, houses, aspects, source, original_input, engine_version, created_at
    chart_json = Column(Text, nullable=False)
    
    # Metadata
    source = Column(String, nullable=False)  # "generated" or "uploaded"
    original_input = Column(Text, nullable=True)  # Original text from user or birth data
    engine_version = Column(String, nullable=True)  # "swisseph vX.X" or "user_uploaded"
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Active status (only one chart can be active per user at a time)
    is_active = Column(Boolean, default=True)


class ConversationMessage(Base):
    """
    Stores conversation thread messages for each user.
    Maintains context for LLM conversations with FIFO management.
    Max 10 messages per user: first 2 (user+assistant) are fixed, remaining 8 are FIFO.
    """
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)  # Message text or summary
    is_first_pair = Column(Boolean, default=False)  # True for first user+assistant messages
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
