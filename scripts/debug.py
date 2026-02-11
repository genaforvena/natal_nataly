"""
Debug Mode Module for Natal Nataly
Implements debug-first architecture with pipeline logging, chart storage, and developer commands.
"""
import os
import json
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.db import SessionLocal
from src.models import PipelineLog, NatalChart, DebugSession, Reading

# Configure logging
logger = logging.getLogger(__name__)

# Debug mode configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEVELOPER_TELEGRAM_ID = os.getenv("DEVELOPER_TELEGRAM_ID", None)

logger.info(f"Debug mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'}")
if DEBUG_MODE and DEVELOPER_TELEGRAM_ID:
    logger.info(f"Developer Telegram ID configured: {DEVELOPER_TELEGRAM_ID}")


def is_developer(telegram_id: str) -> bool:
    """Check if the user is the developer"""
    if not DEBUG_MODE or not DEVELOPER_TELEGRAM_ID:
        return False
    return str(telegram_id) == str(DEVELOPER_TELEGRAM_ID)


def generate_session_id() -> str:
    """Generate unique session ID for pipeline tracking"""
    return str(uuid.uuid4())


def hash_data(data: Any) -> str:
    """Generate SHA256 hash of data for versioning"""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    elif not isinstance(data, str):
        data = str(data)
    return hashlib.sha256(data.encode()).hexdigest()


def hash_prompt(prompt: str) -> str:
    """Generate hash of prompt content for versioning"""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


# ============================================================================
# PIPELINE LOGGING FUNCTIONS
# ============================================================================

def log_pipeline_stage_1_raw_input(
    telegram_id: str,
    raw_user_message: str,
    session_id: Optional[str] = None
) -> str:
    """
    Stage 1: Log raw input from user
    Returns session_id for tracking
    """
    if not DEBUG_MODE:
        return session_id or generate_session_id()
    
    if session_id is None:
        session_id = generate_session_id()
    
    logger.info(f"[PIPELINE] Stage 1: RAW_INPUT - session_id={session_id}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = PipelineLog(
                telegram_id=telegram_id,
                session_id=session_id,
                raw_user_message=raw_user_message,
                timestamp=datetime.now(timezone.utc),
                stage_completed="raw_input"
            )
            session.add(pipeline_log)
            session.commit()
            logger.info(f"[PIPELINE] RAW_INPUT_OK - log_id={pipeline_log.id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] RAW_INPUT_FAILED: {e}")
    
    return session_id


def log_pipeline_stage_2_parsed_data(
    session_id: str,
    parsed_birth_data: Dict[str, Any]
):
    """
    Stage 2: Log parsed birth data from LLM
    Stores complete LLM output before any transformations
    """
    if not DEBUG_MODE:
        return
    
    logger.info(f"[PIPELINE] Stage 2: LLM_PARSE - session_id={session_id}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = session.query(PipelineLog).filter_by(
                session_id=session_id
            ).first()
            
            if pipeline_log:
                pipeline_log.parsed_birth_data_json = json.dumps(parsed_birth_data, indent=2)
                pipeline_log.stage_completed = "parsed"
                session.commit()
                logger.info(f"[PIPELINE] LLM_PARSE_OK - confidence={parsed_birth_data.get('confidence', 'N/A')}")
            else:
                logger.warning(f"[PIPELINE] LLM_PARSE - Pipeline log not found for session_id={session_id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] LLM_PARSE_FAILED: {e}")


def log_pipeline_stage_3_normalized_data(
    session_id: str,
    normalized_birth_data: Dict[str, Any],
    birth_datetime_utc: datetime,
    birth_datetime_local: datetime,
    timezone: str,
    timezone_source: str,
    timezone_validation_status: str,
    coordinates_source: str
):
    """
    Stage 3: Log normalized birth data after system validation
    Includes UTC conversion and timezone validation
    """
    if not DEBUG_MODE:
        return
    
    logger.info(f"[PIPELINE] Stage 3: NORMALIZED - session_id={session_id}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = session.query(PipelineLog).filter_by(
                session_id=session_id
            ).first()
            
            if pipeline_log:
                pipeline_log.normalized_birth_data_json = json.dumps(normalized_birth_data, indent=2)
                pipeline_log.birth_datetime_utc = birth_datetime_utc
                pipeline_log.birth_datetime_local = birth_datetime_local
                pipeline_log.timezone = timezone
                pipeline_log.timezone_source = timezone_source
                pipeline_log.timezone_validation_status = timezone_validation_status
                pipeline_log.coordinates_source = coordinates_source
                pipeline_log.stage_completed = "normalized"
                session.commit()
                logger.info(f"[PIPELINE] NORMALIZED_OK - tz_status={timezone_validation_status}")
                
                if timezone_validation_status == "MISMATCH":
                    logger.warning(f"[PIPELINE] TZ_MISMATCH - Timezone validation failed for session_id={session_id}")
            else:
                logger.warning(f"[PIPELINE] NORMALIZED - Pipeline log not found for session_id={session_id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] NORMALIZED_FAILED: {e}")


def log_pipeline_stage_4_chart_generated(
    session_id: str,
    natal_chart_id: int
):
    """
    Stage 4: Log that natal chart was generated and stored
    """
    if not DEBUG_MODE:
        return
    
    logger.info(f"[PIPELINE] Stage 4: CHART_GENERATED - session_id={session_id}, chart_id={natal_chart_id}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = session.query(PipelineLog).filter_by(
                session_id=session_id
            ).first()
            
            if pipeline_log:
                pipeline_log.natal_chart_id = natal_chart_id
                pipeline_log.stage_completed = "chart_generated"
                session.commit()
                logger.info("[PIPELINE] CHART_GENERATED_OK")
            else:
                logger.warning(f"[PIPELINE] CHART_GENERATED - Pipeline log not found for session_id={session_id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] CHART_GENERATED_FAILED: {e}")


def log_pipeline_stage_5_reading_sent(
    session_id: str,
    reading_id: int
):
    """
    Stage 5: Log that reading was generated and sent
    """
    if not DEBUG_MODE:
        return
    
    logger.info(f"[PIPELINE] Stage 5: READING_SENT - session_id={session_id}, reading_id={reading_id}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = session.query(PipelineLog).filter_by(
                session_id=session_id
            ).first()
            
            if pipeline_log:
                pipeline_log.stage_completed = "reading_sent"
                session.commit()
                logger.info("[PIPELINE] READING_SENT_OK")
            else:
                logger.warning(f"[PIPELINE] READING_SENT - Pipeline log not found for session_id={session_id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] READING_SENT_FAILED: {e}")


def log_pipeline_error(session_id: str, error_message: str):
    """Log pipeline error"""
    if not DEBUG_MODE:
        return
    
    logger.error(f"[PIPELINE] ERROR - session_id={session_id}: {error_message}")
    
    try:
        session = SessionLocal()
        try:
            pipeline_log = session.query(PipelineLog).filter_by(
                session_id=session_id
            ).first()
            
            if pipeline_log:
                pipeline_log.error_message = error_message
                session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"[PIPELINE] ERROR_LOG_FAILED: {e}")


# ============================================================================
# NATAL CHART STORAGE FUNCTIONS
# ============================================================================

def store_natal_chart(
    telegram_id: str,
    birth_data: Dict[str, Any],
    natal_chart: Dict[str, Any],
    engine_version: str,
    ephemeris_version: str = "SE 2.10",
    raw_ephemeris_data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Store complete natal chart with versioning.
    Returns chart_id.
    """
    logger.info(f"Storing natal chart for telegram_id={telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            chart_hash = hash_data(natal_chart)
            
            natal_chart_record = NatalChart(
                telegram_id=telegram_id,
                birth_data_json=json.dumps(birth_data, indent=2),
                natal_chart_json=json.dumps(natal_chart, indent=2),
                engine_version=engine_version,
                ephemeris_version=ephemeris_version,
                chart_hash=chart_hash,
                raw_ephemeris_data=json.dumps(raw_ephemeris_data, indent=2) if raw_ephemeris_data else None
            )
            session.add(natal_chart_record)
            session.commit()
            
            chart_id = natal_chart_record.id
            logger.info(f"Natal chart stored successfully: chart_id={chart_id}, hash={chart_hash[:8]}")
            
            return chart_id
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to store natal chart: {e}")
        raise


def get_natal_chart(chart_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve stored natal chart by ID"""
    try:
        session = SessionLocal()
        try:
            chart_record = session.query(NatalChart).filter_by(id=chart_id).first()
            if chart_record:
                return json.loads(chart_record.natal_chart_json)
            return None
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to retrieve natal chart: {e}")
        return None


def get_user_latest_natal_chart(telegram_id: str) -> Optional[Dict[str, Any]]:
    """Get user's most recent natal chart"""
    try:
        session = SessionLocal()
        try:
            chart_record = session.query(NatalChart).filter_by(
                telegram_id=telegram_id
            ).order_by(NatalChart.created_at.desc()).first()
            
            if chart_record:
                return {
                    "id": chart_record.id,
                    "chart": json.loads(chart_record.natal_chart_json),
                    "birth_data": json.loads(chart_record.birth_data_json),
                    "created_at": chart_record.created_at.isoformat(),
                    "engine_version": chart_record.engine_version,
                    "chart_hash": chart_record.chart_hash
                }
            return None
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to retrieve user's natal chart: {e}")
        return None


# ============================================================================
# LLM PROMPT TRACKING FUNCTIONS
# ============================================================================

def track_reading_prompt(
    reading_id: int,
    prompt_name: str,
    prompt_content: str,
    model_used: str
):
    """Track LLM prompt information for reading reproducibility"""
    if not DEBUG_MODE:
        return
    
    logger.info(f"Tracking prompt for reading_id={reading_id}, prompt={prompt_name}")
    
    try:
        session = SessionLocal()
        try:
            reading = session.query(Reading).filter_by(id=reading_id).first()
            if reading:
                reading.prompt_name = prompt_name
                reading.prompt_hash = hash_prompt(prompt_content)
                reading.model_used = model_used
                session.commit()
                logger.info(f"Prompt tracked successfully for reading_id={reading_id}")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to track prompt: {e}")


# ============================================================================
# DEBUG SESSION MANAGEMENT
# ============================================================================

def create_debug_session(telegram_id: str, session_id: str) -> Optional[int]:
    """Create a new debug session for tracking. Returns session ID or None."""
    if not DEBUG_MODE:
        return None
    
    try:
        session = SessionLocal()
        try:
            debug_session = DebugSession(
                session_id=session_id,
                telegram_id=telegram_id,
                status="in_progress"
            )
            session.add(debug_session)
            session.commit()
            return debug_session.id
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to create debug session: {e}")
        return None


def complete_debug_session(
    session_id: str,
    pipeline_log_id: Optional[int] = None,
    natal_chart_id: Optional[int] = None,
    reading_id: Optional[int] = None
):
    """Mark debug session as completed"""
    if not DEBUG_MODE:
        return
    
    try:
        session = SessionLocal()
        try:
            debug_session = session.query(DebugSession).filter_by(
                session_id=session_id
            ).first()
            
            if debug_session:
                debug_session.completed_at = datetime.now(timezone.utc)
                debug_session.status = "completed"
                if pipeline_log_id:
                    debug_session.pipeline_log_id = pipeline_log_id
                if natal_chart_id:
                    debug_session.natal_chart_id = natal_chart_id
                if reading_id:
                    debug_session.reading_id = reading_id
                session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Failed to complete debug session: {e}")


# ============================================================================
# TIMEZONE VALIDATION
# ============================================================================

def validate_timezone(
    lat: float,
    lng: float,
    llm_timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate timezone by comparing geo lookup with LLM output.
    
    NOTE: Current implementation uses simple coordinate-based estimation.
    For production, integrate a proper timezone library like timezonefinder
    with pytz or zoneinfo module.
    
    Returns:
        dict with keys: timezone, source, validation_status
    """
    logger.info(f"Validating timezone for coordinates: lat={lat}, lng={lng}")
    
    # Simple UTC offset estimation based on longitude
    # TODO: Replace with proper timezone lookup using timezonefinder library
    # This ignores timezone boundaries, DST, and actual timezone definitions
    try:
        # Placeholder: Simple UTC offset estimation
        # Real implementation should use: from timezonefinder import TimezoneFinder
        estimated_offset_hours = int(lng / 15)
        estimated_tz = f"UTC{estimated_offset_hours:+d}"
        
        # If no LLM timezone provided, use estimated
        if not llm_timezone:
            return {
                "timezone": estimated_tz,
                "source": "fallback",
                "validation_status": "NO_VALIDATION",
                "estimated_tz": estimated_tz,
                "llm_tz": None,
                "note": "Simple coordinate-based estimation. Use proper timezone library for production."
            }
        
        # Compare LLM timezone with estimation
        # Note: This will often show MISMATCH due to simplified estimation
        validation_status = "MATCH" if llm_timezone == estimated_tz else "MISMATCH"
        
        if validation_status == "MISMATCH":
            logger.warning(
                f"Timezone mismatch (simplified estimation): "
                f"LLM={llm_timezone}, Estimated={estimated_tz}. "
                f"This may be due to simplified timezone logic. "
                f"Consider implementing proper timezone lookup."
            )
        
        return {
            "timezone": llm_timezone,  # Use LLM timezone as it's likely more accurate
            "source": "llm",  # Changed from "api" to be more accurate
            "validation_status": validation_status,
            "estimated_tz": estimated_tz,
            "llm_tz": llm_timezone,
            "note": "Validation uses simplified estimation. MISMATCH may be false positive."
        }
    except Exception as e:
        logger.exception(f"Timezone validation failed: {e}")
        return {
            "timezone": llm_timezone or "UTC+0",
            "source": "fallback",
            "validation_status": "ERROR",
            "error": str(e)
        }
