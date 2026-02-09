import os
import json
import httpx
import logging
from datetime import datetime, timezone
from astrology import generate_natal_chart, get_engine_version
from llm import extract_birth_data, generate_clarification_question, interpret_chart, classify_intent, generate_assistant_response
from db import SessionLocal
from models import User, BirthData, Reading, AstroProfile, UserNatalChart
from models import STATE_AWAITING_BIRTH_DATA, STATE_AWAITING_CLARIFICATION, STATE_AWAITING_CONFIRMATION, STATE_AWAITING_EDIT_CONFIRMATION, STATE_HAS_CHART, STATE_CHATTING_ABOUT_CHART
from debug import (
    DEBUG_MODE, 
    log_pipeline_stage_1_raw_input,
    log_pipeline_stage_2_parsed_data,
    log_pipeline_stage_3_normalized_data,
    log_pipeline_stage_4_chart_generated,
    log_pipeline_stage_5_reading_sent,
    log_pipeline_error,
    store_natal_chart,
    validate_timezone,
    track_reading_prompt,
    create_debug_session,
    complete_debug_session
)
from debug_commands import handle_debug_command
from user_commands import handle_user_command
from chart_parser import parse_uploaded_chart, validate_chart_data

# Configure logging
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Validate bot token is configured
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
else:
    logger.info(f"Bot initialized with Telegram token configured")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

logger.info(f"Telegram API URL configured")

async def send_telegram_message(chat_id: int, text: str):
    """Send a message to Telegram using HTTP API"""
    logger.debug(f"Sending message to chat_id={chat_id}, text_length={len(text)}")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json=payload
            )
            # Check if the request was successful (2xx status codes)
            if response.is_success:
                logger.info(f"Message sent successfully to chat_id={chat_id}, status={response.status_code}")
                return response
            elif response.status_code == 404:
                # 404 typically means the chat doesn't exist, user blocked the bot, or invalid chat_id
                # This is not a critical error - log it and return None without raising
                logger.warning(f"Cannot send message to chat_id={chat_id}: Chat not found (404). User may have blocked the bot or chat_id is invalid.")
                logger.debug(f"404 Response details: {response.text}")
                return None
            else:
                logger.error(f"Failed to send message to chat_id={chat_id}, status={response.status_code}, response={response.text}")
                raise Exception(f"Telegram API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.exception(f"Error sending Telegram message to chat_id={chat_id}: {e}")
        raise


def get_or_create_user(session, telegram_id: str) -> User:
    """Get existing user or create new one"""
    logger.debug(f"Getting or creating user with telegram_id={telegram_id}")
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            logger.debug(f"Updating existing user: {telegram_id}")
            user.last_seen = datetime.now(timezone.utc)
        else:
            logger.info(f"Creating new user: {telegram_id}")
            user = User(telegram_id=telegram_id, state=STATE_AWAITING_BIRTH_DATA)
            session.add(user)
        session.commit()
        logger.debug(f"User retrieved/created successfully: {telegram_id}, state={user.state}")
        return user
    except Exception as e:
        logger.exception(f"Error getting/creating user {telegram_id}: {e}")
        raise


def update_user_state(session, telegram_id: str, state: str, natal_chart_json: str = None, missing_fields: str = None):
    """Update user state and optional fields"""
    logger.debug(f"Updating user state: telegram_id={telegram_id}, new_state={state}")
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.state = state
            if natal_chart_json is not None:
                user.natal_chart_json = natal_chart_json
            if missing_fields is not None:
                user.missing_fields = missing_fields
            user.last_seen = datetime.now(timezone.utc)
            session.commit()
            logger.info(f"User state updated: {telegram_id} -> {state}")
        else:
            logger.warning(f"User {telegram_id} not found for state update")
    except Exception as e:
        logger.exception(f"Error updating user state {telegram_id}: {e}")
        raise


def save_birth_data(session, telegram_id: str, birth_data: dict):
    """Save birth data to database"""
    logger.debug(f"Saving birth data for telegram_id={telegram_id}")
    try:
        birth_record = BirthData(
            telegram_id=telegram_id,
            dob=birth_data["dob"],
            time=birth_data["time"],
            lat=birth_data["lat"],
            lng=birth_data["lng"]
        )
        session.add(birth_record)
        session.commit()
        logger.info(f"Birth data saved successfully for telegram_id={telegram_id}")
        return birth_record
    except Exception as e:
        logger.exception(f"Error saving birth data for {telegram_id}: {e}")
        raise


def save_reading(session, telegram_id: str, reading_text: str, birth_data_id: int = None):
    """Save reading to database"""
    logger.debug(f"Saving reading for telegram_id={telegram_id}")
    try:
        reading_record = Reading(
            telegram_id=telegram_id,
            birth_data_id=birth_data_id,
            reading_text=reading_text,
            delivered=False
        )
        session.add(reading_record)
        session.commit()
        logger.info(f"Reading saved successfully for telegram_id={telegram_id}, reading_id={reading_record.id}")
        return reading_record
    except Exception as e:
        logger.exception(f"Error saving reading for {telegram_id}: {e}")
        raise


def mark_reading_delivered(session, reading_id: int):
    """Mark a reading as delivered"""
    logger.debug(f"Marking reading {reading_id} as delivered")
    try:
        reading = session.query(Reading).filter_by(id=reading_id).first()
        if reading:
            reading.delivered = True
            reading.delivered_at = datetime.now(timezone.utc)
            session.commit()
            logger.info(f"Reading {reading_id} marked as delivered")
        else:
            logger.warning(f"Reading {reading_id} not found for marking as delivered")
    except Exception as e:
        logger.exception(f"Error marking reading {reading_id} as delivered: {e}")
        raise


# ============================================================================
# PROFILE MANAGEMENT FUNCTIONS
# ============================================================================

def get_active_profile(session, user: User):
    """
    Get user's active AstroProfile or None.
    
    Returns:
        AstroProfile object or None if no active profile
    """
    logger.debug(f"Getting active profile for user {user.telegram_id}")
    try:
        if user.active_profile_id:
            profile = session.query(AstroProfile).filter_by(id=user.active_profile_id).first()
            if profile:
                logger.info(f"Active profile found: id={profile.id}, type={profile.profile_type}")
                return profile
            else:
                logger.warning(f"Active profile ID {user.active_profile_id} not found, resetting")
                user.active_profile_id = None
                session.commit()
        
        logger.info(f"No active profile for user {user.telegram_id}")
        return None
    except Exception as e:
        logger.exception(f"Error getting active profile: {e}")
        raise


def create_profile(session, telegram_id: str, birth_data: dict, natal_chart: dict, 
                  profile_name: str = None, profile_type: str = "self") -> AstroProfile:
    """
    Create a new AstroProfile.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        birth_data: Dict with dob, time, lat, lng
        natal_chart: Generated natal chart dict
        profile_name: Optional name for the profile
        profile_type: Type of profile (self|partner|friend|analysis)
        
    Returns:
        Created AstroProfile object
    """
    logger.info(f"Creating new profile for user {telegram_id}, type={profile_type}, name={profile_name}")
    try:
        profile = AstroProfile(
            telegram_id=telegram_id,
            name=profile_name,
            profile_type=profile_type,
            birth_data_json=json.dumps(birth_data),
            natal_chart_json=json.dumps(natal_chart)
        )
        session.add(profile)
        session.commit()
        logger.info(f"Profile created successfully: id={profile.id}")
        return profile
    except Exception as e:
        logger.exception(f"Error creating profile: {e}")
        raise


def set_active_profile(session, user: User, profile_id: int):
    """
    Set the active profile for a user.
    
    Args:
        session: Database session
        user: User object
        profile_id: ID of the profile to activate
    """
    logger.info(f"Setting active profile {profile_id} for user {user.telegram_id}")
    try:
        # Verify profile exists and belongs to user
        profile = session.query(AstroProfile).filter_by(
            id=profile_id,
            telegram_id=user.telegram_id
        ).first()
        
        if not profile:
            logger.error(f"Profile {profile_id} not found or doesn't belong to user {user.telegram_id}")
            raise ValueError(f"Profile not found")
        
        user.active_profile_id = profile_id
        session.commit()
        logger.info(f"Active profile set successfully")
    except Exception as e:
        logger.exception(f"Error setting active profile: {e}")
        raise


def list_user_profiles(session, telegram_id: str):
    """
    Get all profiles for a user.
    
    Returns:
        List of AstroProfile objects
    """
    logger.debug(f"Listing profiles for user {telegram_id}")
    try:
        profiles = session.query(AstroProfile).filter_by(telegram_id=telegram_id).order_by(AstroProfile.created_at).all()
        logger.info(f"Found {len(profiles)} profiles for user {telegram_id}")
        return profiles
    except Exception as e:
        logger.exception(f"Error listing profiles: {e}")
        raise


def build_agent_context(session, user: User, profile: AstroProfile = None) -> dict:
    """
    Build context for assistant response.
    
    Args:
        session: Database session
        user: User object
        profile: Optional active profile
        
    Returns:
        Dict with natal_chart, profile_name, recent_questions, etc.
    """
    logger.debug(f"Building agent context for user {user.telegram_id}")
    try:
        context = {
            "natal_chart": None,
            "profile_name": None,
            "recent_questions": [],
            "assistant_mode": user.assistant_mode
        }
        
        if profile:
            context["natal_chart"] = json.loads(profile.natal_chart_json) if profile.natal_chart_json else None
            context["profile_name"] = profile.name or "Self"
            
            # Get last 5 readings for context
            recent_readings = session.query(Reading).filter_by(
                telegram_id=user.telegram_id
            ).order_by(Reading.created_at.desc()).limit(5).all()
            
            context["recent_questions"] = [r.reading_text[:100] for r in recent_readings]
        
        logger.debug(f"Context built: has_chart={context['natal_chart'] is not None}, profile={context['profile_name']}")
        return context
    except Exception as e:
        logger.exception(f"Error building agent context: {e}")
        raise


def create_and_activate_profile(session, user: User, birth_data: dict, chart: dict) -> AstroProfile:
    """
    Helper function to create a new profile, set it as active, and update user state.
    
    Args:
        session: Database session
        user: User object
        birth_data: Birth data dict
        chart: Generated natal chart dict
        
    Returns:
        Created AstroProfile
    """
    logger.info(f"Creating and activating profile for user {user.telegram_id}")
    
    # Save birth data for legacy support
    birth_record = save_birth_data(session, user.telegram_id, birth_data)
    
    # Create new AstroProfile
    profile = create_profile(
        session, 
        user.telegram_id, 
        birth_data, 
        chart,
        profile_name=None,  # Default profile has no special name
        profile_type="self"
    )
    
    # Set as active profile
    set_active_profile(session, user, profile.id)
    
    # Store natal chart in user for legacy compatibility
    chart_json = json.dumps(chart)
    update_user_state(session, user.telegram_id, STATE_HAS_CHART, natal_chart_json=chart_json)
    
    return profile


async def handle_awaiting_birth_data(session, user: User, chat_id: int, text: str):
    """Handle messages when user is in awaiting_birth_data state"""
    logger.info(f"Handling awaiting_birth_data for user {user.telegram_id}")
    
    # Stage 1: Log raw input
    session_id = log_pipeline_stage_1_raw_input(user.telegram_id, text)
    if DEBUG_MODE:
        create_debug_session(user.telegram_id, session_id)
    
    try:
        # Use LLM to extract birth data from free-form text
        birth_data = extract_birth_data(text)
        
        # Stage 2: Log parsed data from LLM
        log_pipeline_stage_2_parsed_data(session_id, birth_data)
        
        # Check if any required fields are missing
        missing = birth_data.get("missing_fields", [])
        
        if missing:
            logger.info(f"Missing fields detected: {missing}")
            # Update state to awaiting_clarification
            update_user_state(session, user.telegram_id, STATE_AWAITING_CLARIFICATION, missing_fields=",".join(missing))
            
            # Generate clarification question
            question = generate_clarification_question(missing, text)
            await send_telegram_message(chat_id, question)
            return
        
        # All data is present, validate it
        if not all([birth_data.get("dob"), birth_data.get("time"), 
                   birth_data.get("lat") is not None, birth_data.get("lng") is not None]):
            logger.warning("Birth data extraction returned data but with null values")
            log_pipeline_error(session_id, "Birth data extraction returned null values")
            await send_telegram_message(
                chat_id,
                "Пожалуйста, укажите дату рождения (YYYY-MM-DD), время (HH:MM) и место (город или координаты)."
            )
            return
        
        # Stage 3: Normalize and validate data
        # Validate timezone
        tz_validation = validate_timezone(
            birth_data["lat"],
            birth_data["lng"],
            birth_data.get("timezone")
        )
        
        # Create normalized birth data
        normalized_birth_data = {
            "dob": birth_data["dob"],
            "time": birth_data["time"],
            "lat": birth_data["lat"],
            "lng": birth_data["lng"],
            "timezone": tz_validation["timezone"],
            "timezone_source": tz_validation["source"],
            "timezone_validation_status": tz_validation["validation_status"],
            "location": birth_data.get("location", "Unknown")
        }
        
        # Calculate UTC and local times
        # TODO: Implement proper UTC conversion using timezone from tz_validation
        # Currently just using local time as placeholder
        birth_datetime_local = datetime.strptime(f"{birth_data['dob']} {birth_data['time']}", "%Y-%m-%d %H:%M")
        # Note: This is a placeholder. Real UTC conversion requires proper timezone handling
        birth_datetime_utc = birth_datetime_local  # FIXME: Should convert using validated timezone
        
        log_pipeline_stage_3_normalized_data(
            session_id,
            normalized_birth_data,
            birth_datetime_utc,
            birth_datetime_local,
            tz_validation["timezone"],
            tz_validation["source"],
            tz_validation["validation_status"],
            "user_input"
        )
        
        # Store pending data in user record for confirmation
        user.pending_birth_data = json.dumps(birth_data)
        user.pending_normalized_data = json.dumps(normalized_birth_data)
        user.state = STATE_AWAITING_CONFIRMATION
        session.commit()
        
        # Show confirmation message
        confirmation_msg = "✨ **Please confirm your birth data:**\n\n"
        confirmation_msg += f"**Date (local):** {birth_data['dob']}\n"
        confirmation_msg += f"**Time (local):** {birth_data['time']}\n"
        confirmation_msg += f"**Location:** {birth_data.get('location', 'Not specified')}\n"
        confirmation_msg += f"**Timezone:** {tz_validation['timezone']}\n"
        confirmation_msg += f"**Coordinates:** {birth_data['lat']}, {birth_data['lng']}\n"
        
        if birth_datetime_utc:
            confirmation_msg += f"**UTC time:** {birth_datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        confirmation_msg += f"\n**Timezone Source:** {tz_validation['source']}\n"
        
        confirmation_msg += "\n⚠️ Please verify this data carefully. Incorrect data will result in inaccurate readings.\n\n"
        confirmation_msg += "Reply **CONFIRM** to proceed or **EDIT** to change the data."
        
        await send_telegram_message(chat_id, confirmation_msg)
        
        logger.info(f"Birth data pending confirmation for user {user.telegram_id}")
        
    except Exception as e:
        logger.exception(f"Error handling awaiting_birth_data: {e}")
        log_pipeline_error(session_id, str(e))
        await send_telegram_message(
            chat_id,
            "Произошла ошибка при обработке данных. Пожалуйста, попробуйте ещё раз."
        )


async def handle_awaiting_confirmation(session, user: User, chat_id: int, text: str):
    """Handle confirmation of birth data"""
    logger.info(f"Handling awaiting_confirmation for user {user.telegram_id}")
    
    text_upper = text.strip().upper()
    
    if text_upper == "CONFIRM":
        try:
            # Retrieve pending data
            if not user.pending_birth_data or not user.pending_normalized_data:
                await send_telegram_message(chat_id, "Нет данных для подтверждения. Пожалуйста, отправь данные рождения заново.")
                user.state = STATE_AWAITING_BIRTH_DATA
                session.commit()
                return
            
            birth_data = json.loads(user.pending_birth_data)
            normalized_birth_data = json.loads(user.pending_normalized_data)
            
            # Generate natal chart
            logger.info(f"Generating natal chart for user {user.telegram_id}")
            original_input = f"DOB: {birth_data['dob']}, Time: {birth_data['time']}, Lat: {birth_data['lat']}, Lng: {birth_data['lng']}"
            chart = generate_natal_chart(
                birth_data["dob"],
                birth_data["time"],
                birth_data["lat"],
                birth_data["lng"],
                original_input=original_input
            )
            
            # Store natal chart with versioning (legacy NatalChart table)
            chart_id = store_natal_chart(
                user.telegram_id,
                birth_data,
                chart,
                get_engine_version(),
                "SE 2.10"  # Swiss Ephemeris version
            )
            
            # Store in unified UserNatalChart table (new source of truth)
            # First, deactivate any existing active charts
            session.query(UserNatalChart).filter_by(
                telegram_id=user.telegram_id,
                is_active=True
            ).update({"is_active": False})
            
            # Create new chart record
            user_chart = UserNatalChart(
                telegram_id=user.telegram_id,
                chart_json=json.dumps(chart, ensure_ascii=False),
                source="generated",
                original_input=original_input,
                engine_version=chart.get("engine_version", get_engine_version()),
                is_active=True
            )
            session.add(user_chart)
            
            # Create profile and set as active
            create_and_activate_profile(session, user, birth_data, chart)
            
            # Clear pending data
            user.pending_birth_data = None
            user.pending_normalized_data = None
            session.commit()
            
            # Send success message
            await send_telegram_message(
                chat_id,
                "✅ Натальная карта создана!\n\n"
                "Теперь ты можешь:\n"
                "• Задавать вопросы о своей карте\n"
                "• Использовать /my_data чтобы увидеть свои данные\n"
                "• Использовать /my_chart_raw для получения сырых данных карты\n"
                "• Использовать /my_readings для просмотра своих readings"
            )
            
            logger.info(f"Chart confirmed and created for user {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Error confirming birth data: {e}")
            await send_telegram_message(
                chat_id,
                "Произошла ошибка при создании карты. Пожалуйста, попробуйте ещё раз."
            )
            user.state = STATE_AWAITING_BIRTH_DATA
            session.commit()
    
    elif text_upper == "EDIT":
        # Clear pending data and go back to input
        user.pending_birth_data = None
        user.pending_normalized_data = None
        user.state = STATE_AWAITING_BIRTH_DATA
        session.commit()
        
        await send_telegram_message(
            chat_id,
            "✏️ Хорошо, давай попробуем ещё раз.\n\n"
            "Отправь данные рождения в формате:\n"
            "DOB: YYYY-MM-DD\n"
            "Time: HH:MM\n"
            "Lat: XX.XXXX\n"
            "Lng: XX.XXXX"
        )
    
    else:
        # Invalid response
        await send_telegram_message(
            chat_id,
            "⚠️ Пожалуйста, ответь **CONFIRM** для подтверждения или **EDIT** для изменения данных."
        )


async def handle_awaiting_chart_upload(session, user: User, chat_id: int, text: str):
    """Handle uploaded chart text"""
    logger.info(f"Handling awaiting_chart_upload for user {user.telegram_id}")
    
    # Check for cancel command
    if text.strip().upper() == "/CANCEL":
        user.state = STATE_HAS_CHART
        session.commit()
        await send_telegram_message(chat_id, "❌ Upload cancelled.")
        return
    
    try:
        # Try to parse the uploaded chart
        logger.info("Attempting to parse uploaded chart")
        chart = parse_uploaded_chart(text, format_hint="auto")
        
        # Validate chart data
        validate_chart_data(chart)
        
        # Store chart in UserNatalChart table
        # First, deactivate any existing active charts
        session.query(UserNatalChart).filter_by(
            telegram_id=user.telegram_id,
            is_active=True
        ).update({"is_active": False})
        
        # Create new chart record
        user_chart = UserNatalChart(
            telegram_id=user.telegram_id,
            chart_json=json.dumps(chart, ensure_ascii=False),
            source="uploaded",
            original_input=text[:1000],  # Store first 1000 chars
            engine_version=chart.get("engine_version", "user_uploaded"),
            is_active=True
        )
        session.add(user_chart)
        
        # Update user state
        user.state = STATE_HAS_CHART
        session.commit()
        
        # Send success message with chart summary
        planets_count = len(chart.get("planets", {}))
        houses_count = len(chart.get("houses", {}))
        aspects_count = len(chart.get("aspects", []))
        
        success_msg = "✅ **Chart uploaded successfully!**\n\n"
        success_msg += f"📊 **Chart Summary:**\n"
        success_msg += f"• Planets: {planets_count}\n"
        success_msg += f"• Houses: {houses_count}\n"
        success_msg += f"• Aspects: {aspects_count}\n\n"
        
        # Show some key planets
        if "Sun" in chart["planets"]:
            sun = chart["planets"]["Sun"]
            success_msg += f"☀️ Sun: {sun['deg']:.2f}° {sun['sign']}, House {sun['house']}\n"
        
        if "Moon" in chart["planets"]:
            moon = chart["planets"]["Moon"]
            success_msg += f"🌙 Moon: {moon['deg']:.2f}° {moon['sign']}, House {moon['house']}\n"
        
        if "Ascendant" in chart["planets"]:
            asc = chart["planets"]["Ascendant"]
            success_msg += f"⬆️ Ascendant: {asc['deg']:.2f}° {asc['sign']}\n"
        
        success_msg += "\n✨ Your chart is now ready! You can:\n"
        success_msg += "• Ask questions about your chart\n"
        success_msg += "• Use /my_chart_raw to see the full chart data\n"
        success_msg += "• Use /my_readings to view your readings"
        
        await send_telegram_message(chat_id, success_msg)
        logger.info(f"Chart uploaded successfully for user {user.telegram_id}")
        
    except ValueError as e:
        # Parsing error
        logger.warning(f"Chart parsing failed: {e}")
        await send_telegram_message(
            chat_id,
            f"❌ **Failed to parse chart:**\n{str(e)}\n\n"
            "Please make sure your chart is in the correct format:\n"
            "```\n"
            "Sun: 10°30' Capricorn, House 4\n"
            "Moon: 10°10' Libra, House 1\n"
            "...\n"
            "```\n\n"
            "Type /cancel to cancel upload, or send corrected chart data."
        )
    except Exception as e:
        logger.exception(f"Error handling chart upload: {e}")
        await send_telegram_message(
            chat_id,
            "Произошла ошибка при обработке карты. Попробуйте ещё раз или используйте /cancel для отмены."
        )


async def handle_awaiting_clarification(session, user: User, chat_id: int, text: str):
    """Handle messages when user is in awaiting_clarification state"""
    logger.info(f"Handling awaiting_clarification for user {user.telegram_id}")
    
    try:
        # Extract data again from the clarification message
        birth_data = extract_birth_data(text)
        
        # Check what was previously missing
        previously_missing = user.missing_fields.split(",") if user.missing_fields else []
        logger.debug(f"Previously missing fields: {previously_missing}")
        
        # Check if still missing anything
        still_missing = birth_data.get("missing_fields", [])
        
        if still_missing:
            logger.info(f"Still missing fields: {still_missing}")
            # Update missing fields
            update_user_state(session, user.telegram_id, STATE_AWAITING_CLARIFICATION, missing_fields=",".join(still_missing))
            
            # Ask again
            question = generate_clarification_question(still_missing, text)
            await send_telegram_message(chat_id, question)
            return
        
        # All data is now present
        if not all([birth_data.get("dob"), birth_data.get("time"), 
                   birth_data.get("lat") is not None, birth_data.get("lng") is not None]):
            logger.warning("Birth data still incomplete after clarification")
            await send_telegram_message(
                chat_id,
                "Пожалуйста, укажите все необходимые данные: дату, время и место рождения."
            )
            return
        
        # Generate natal chart
        logger.info(f"Generating natal chart for user {user.telegram_id}")
        chart = generate_natal_chart(
            birth_data["dob"],
            birth_data["time"],
            birth_data["lat"],
            birth_data["lng"]
        )
        
        # Create profile and set as active
        create_and_activate_profile(session, user, birth_data, chart)
        
        # Clear missing fields
        update_user_state(session, user.telegram_id, STATE_HAS_CHART, missing_fields=None)
        
        # Send confirmation message
        await send_telegram_message(
            chat_id,
            "✨ Натальная карта готова.\nТеперь ты можешь задавать любые вопросы о себе."
        )
        
        logger.info(f"Clarification completed successfully for user {user.telegram_id}")
        
    except Exception as e:
        logger.exception(f"Error handling awaiting_clarification: {e}")
        await send_telegram_message(
            chat_id,
            "Произошла ошибка при обработке данных. Пожалуйста, попробуйте ещё раз."
        )


async def handle_chatting_about_chart(session, user: User, chat_id: int, text: str):
    """Handle messages when user has a chart and is asking questions"""
    logger.info(f"Handling chatting_about_chart for user {user.telegram_id}")
    
    try:
        # Get active profile
        profile = get_active_profile(session, user)
        
        if not profile or not profile.natal_chart_json:
            # Fallback to legacy chart stored in user
            if not user.natal_chart_json:
                logger.error(f"User {user.telegram_id} in chatting state but no chart found")
                await send_telegram_message(
                    chat_id,
                    "Кажется, у меня нет твоей натальной карты. Пожалуйста, предоставь данные рождения снова."
                )
                update_user_state(session, user.telegram_id, STATE_AWAITING_BIRTH_DATA)
                return
            
            # Create profile from legacy data if needed
            chart = json.loads(user.natal_chart_json)
            # We don't have birth data in this case, so we'll use what we have
            logger.warning("Using legacy chart data without full birth data")
        else:
            chart = json.loads(profile.natal_chart_json)
        
        # Update state to chatting_about_chart if it was has_chart
        if user.state == STATE_HAS_CHART:
            update_user_state(session, user.telegram_id, STATE_CHATTING_ABOUT_CHART)
        
        # Build context for assistant
        context = build_agent_context(session, user, profile)
        
        # Get assistant response using new assistant mode
        prompt_name = "assistant_response"
        if user.assistant_mode:
            logger.info(f"Using assistant mode for response")
            reading = generate_assistant_response(context, text)
        else:
            # Fallback to legacy interpret_chart
            logger.info(f"Using legacy chart interpretation")
            reading = interpret_chart(chart, question=text)
            prompt_name = "astrologer_chat"
        
        # Save reading to database
        reading_record = save_reading(session, user.telegram_id, reading)
        reading_id = reading_record.id
        
        # Track LLM prompt for reproducibility
        from llm import MODEL, get_prompt
        try:
            # Use correct prompt name based on mode
            if user.assistant_mode:
                prompt_file = "assistant_personality.system"
            else:
                prompt_file = "astrologer_chat.system"
            
            prompt_content = get_prompt(prompt_file)
            track_reading_prompt(reading_id, prompt_name, prompt_content, MODEL)
        except Exception as e:
            logger.warning(f"Failed to track reading prompt: {e}")
        
        # Send reading to user
        response = await send_telegram_message(chat_id, reading)
        
        # Mark as delivered if successful
        if response is not None:
            mark_reading_delivered(session, reading_id)
        
        logger.info(f"Chart interpretation sent successfully for user {user.telegram_id}")
        
    except Exception as e:
        logger.exception(f"Error handling chatting_about_chart: {e}")
        await send_telegram_message(
            chat_id,
            "Произошла ошибка при обработке вопроса. Пожалуйста, попробуйте ещё раз."
        )


# ============================================================================
# INTENT-BASED HANDLERS
# ============================================================================

async def handle_profiles_command(session, user: User, chat_id: int):
    """Handle /profiles command to list all user profiles"""
    logger.info(f"Handling /profiles command for user {user.telegram_id}")
    
    try:
        profiles = list_user_profiles(session, user.telegram_id)
        
        if not profiles:
            await send_telegram_message(chat_id, "У тебя пока нет ни одного профиля. Отправь данные рождения, чтобы создать первый профиль.")
            return
        
        # Build profiles list message
        message = "📋 Твои профили:\n\n"
        
        for profile in profiles:
            is_active = (profile.id == user.active_profile_id)
            indicator = "✅ " if is_active else "   "
            name = profile.name or "Ты"
            profile_type = profile.profile_type.capitalize()
            
            message += f"{indicator}{name} ({profile_type})\n"
        
        message += "\nЧтобы переключиться на другой профиль, просто скажи 'переключись на [имя]'"
        
        await send_telegram_message(chat_id, message)
        
    except Exception as e:
        logger.exception(f"Error handling profiles command: {e}")
        await send_telegram_message(chat_id, "Ошибка при получении списка профилей.")


async def handle_meta_conversation(session, user: User, chat_id: int, text: str):
    """Handle meta conversation like greetings, casual chat"""
    logger.info(f"Handling meta_conversation for user {user.telegram_id}")
    
    try:
        # Build minimal context for assistant
        profile = get_active_profile(session, user)
        context = build_agent_context(session, user, profile)
        
        # Use assistant to respond naturally
        reading = generate_assistant_response(context, text)
        await send_telegram_message(chat_id, reading)
        
    except Exception as e:
        logger.exception(f"Error handling meta conversation: {e}")
        await send_telegram_message(chat_id, "Привет! Я твой личный астрологический ассистент. Чем могу помочь?")


async def handle_general_question(session, user: User, chat_id: int, text: str):
    """Handle general astrology questions not specific to user's chart"""
    logger.info(f"Handling ask_general_question for user {user.telegram_id}")
    
    try:
        # Build context
        profile = get_active_profile(session, user)
        context = build_agent_context(session, user, profile)
        
        # Use assistant to explain general astrology
        reading = generate_assistant_response(context, text)
        await send_telegram_message(chat_id, reading)
        
    except Exception as e:
        logger.exception(f"Error handling general question: {e}")
        await send_telegram_message(chat_id, "Произошла ошибка. Попробуй переформулировать вопрос.")


async def route_message(session, user: User, chat_id: int, text: str):
    """
    Route message based on user state and intent classification.
    Uses intent classification for users with charts to enable conversational flow.
    """
    logger.info(f"Routing message for user {user.telegram_id}, state={user.state}")
    
    # For users in data collection states, use traditional state-based routing
    if user.state == STATE_AWAITING_BIRTH_DATA:
        await handle_awaiting_birth_data(session, user, chat_id, text)
        return
    elif user.state == STATE_AWAITING_CLARIFICATION:
        await handle_awaiting_clarification(session, user, chat_id, text)
        return
    elif user.state == STATE_AWAITING_CONFIRMATION:
        await handle_awaiting_confirmation(session, user, chat_id, text)
        return
    elif user.state == "awaiting_chart_upload":
        await handle_awaiting_chart_upload(session, user, chat_id, text)
        return
    
    # For users with charts, use intent-based routing for conversational flow
    if user.state in [STATE_HAS_CHART, STATE_CHATTING_ABOUT_CHART]:
        try:
            # Classify intent
            intent_result = classify_intent(text)
            intent = intent_result.get("intent", "unknown")
            confidence = intent_result.get("confidence", 0.0)
            
            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            
            # Route based on intent
            if intent == "provide_birth_data":
                # User wants to provide new birth data (maybe for a new profile)
                logger.info("User providing new birth data, switching to awaiting_birth_data state")
                update_user_state(session, user.telegram_id, STATE_AWAITING_BIRTH_DATA)
                await handle_awaiting_birth_data(session, user, chat_id, text)
                
            elif intent == "ask_about_chart":
                # User asking about their chart - use assistant mode
                await handle_chatting_about_chart(session, user, chat_id, text)
                
            elif intent == "ask_general_question":
                # General astrology question
                await handle_general_question(session, user, chat_id, text)
                
            elif intent == "meta_conversation":
                # Casual conversation, greetings
                await handle_meta_conversation(session, user, chat_id, text)
                
            elif intent == "new_profile_request":
                # User wants to create a new profile
                await send_telegram_message(
                    chat_id,
                    "Отлично! Давай создадим новый профиль. Отправь мне данные рождения: дату, время и место."
                )
                # Switch to awaiting birth data state but remember we're creating a new profile
                update_user_state(session, user.telegram_id, STATE_AWAITING_BIRTH_DATA)
                
            elif intent == "switch_profile":
                # User wants to switch profiles
                profiles = list_user_profiles(session, user.telegram_id)
                if len(profiles) <= 1:
                    await send_telegram_message(
                        chat_id,
                        "У тебя пока только один профиль. Хочешь создать ещё один?"
                    )
                else:
                    await handle_profiles_command(session, user, chat_id)
                    await send_telegram_message(
                        chat_id,
                        "Выбери профиль, назвав его имя или номер."
                    )
                    
            elif intent == "clarify_birth_data":
                # User provided clarification-style response outside clarification flow - treat as chart question
                await handle_chatting_about_chart(session, user, chat_id, text)
                
            else:
                # Unknown or low confidence - default to chatting about chart
                logger.warning(f"Unknown or low confidence intent, defaulting to chart chat")
                await handle_chatting_about_chart(session, user, chat_id, text)
                
        except Exception as e:
            logger.exception(f"Error in intent-based routing: {e}")
            # Fallback to traditional routing
            await handle_chatting_about_chart(session, user, chat_id, text)
    else:
        logger.error(f"Unknown user state: {user.state}")
        await send_telegram_message(chat_id, "Произошла ошибка. Пожалуйста, начните сначала с предоставления данных рождения.")
        update_user_state(session, user.telegram_id, STATE_AWAITING_BIRTH_DATA)


async def handle_telegram_update(update: dict):
    """
    Entry point for Telegram webhook updates.
    Routes messages based on user state.
    """
    logger.info(f"=== Processing Telegram update ===")
    update_type = "message" if "message" in update else "other"
    logger.debug(f"Update type: {update_type}")
    
    try:
        # Extract message data
        if "message" not in update:
            logger.warning("Update does not contain a message, skipping")
            return {"ok": True}
        
        message = update["message"]
        
        # Validate message structure
        if "chat" not in message or "id" not in message["chat"]:
            logger.error(f"Invalid message structure: missing chat.id")
            return {"ok": True}
        
        if "from" not in message or "id" not in message["from"]:
            logger.error(f"Invalid message structure: missing from.id")
            return {"ok": True}
        
        chat_id = message["chat"]["id"]
        telegram_id = str(message["from"]["id"])
        text = message.get("text", "")
        
        logger.info(f"Processing message from chat_id={chat_id}, telegram_id={telegram_id}")
        logger.debug(f"Message length: {len(text)} characters")
        
        # Get or create user
        session = SessionLocal()
        try:
            user = get_or_create_user(session, telegram_id)
            
            # Check for commands first
            if text.startswith("/"):
                # Create send_msg helper function for command handlers
                async def send_msg(msg):
                    await send_telegram_message(chat_id, msg)
                
                # Check for debug commands
                if await handle_debug_command(telegram_id, text, send_msg):
                    logger.info(f"=== Update processed successfully (debug command) for telegram_id={telegram_id} ===")
                    return {"ok": True}
                
                # Check for user transparency commands
                if await handle_user_command(telegram_id, text, send_msg):
                    logger.info(f"=== Update processed successfully (user command) for telegram_id={telegram_id} ===")
                    return {"ok": True}
                
                # Handle other commands
                if text.startswith("/profiles"):
                    await handle_profiles_command(session, user, chat_id)
                    logger.info(f"=== Update processed successfully (command) for telegram_id={telegram_id} ===")
                    return {"ok": True}
            
            # Route message based on state
            await route_message(session, user, chat_id, text)
            
            logger.info(f"=== Update processed successfully for telegram_id={telegram_id} ===")
        finally:
            session.close()
        
        return {"ok": True}
        
    except Exception as e:
        logger.exception(f"Critical error handling update: {e}")
        return {"ok": True}
