import os
import re
import httpx
import logging
from datetime import datetime
from astrology import generate_natal_chart
from llm import interpret_chart
from db import SessionLocal
from models import User, BirthData, Reading

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

# Expected format:
# DOB: YYYY-MM-DD
# Time: HH:MM
# Lat: xx.xxxx
# Lng: xx.xxxx

FORMAT_EXAMPLE = """Invalid format. Please use:
DOB: YYYY-MM-DD
Time: HH:MM
Lat: xx.xxxx
Lng: xx.xxxx

Example:
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060"""

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

def parse_birth_data(text: str):
    """Parse birth data from user message"""
    # Log only message length, not the actual sensitive content
    logger.debug(f"Parsing birth data from message (length: {len(text)} chars)")
    
    dob_pattern = r"DOB:\s*(\d{4}-\d{2}-\d{2})"
    time_pattern = r"Time:\s*(\d{2}:\d{2})"
    lat_pattern = r"Lat:\s*([-]?\d+\.?\d*)"
    lng_pattern = r"Lng:\s*([-]?\d+\.?\d*)"
    
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    time_match = re.search(time_pattern, text, re.IGNORECASE)
    lat_match = re.search(lat_pattern, text, re.IGNORECASE)
    lng_match = re.search(lng_pattern, text, re.IGNORECASE)
    
    if not all([dob_match, time_match, lat_match, lng_match]):
        logger.warning(f"Failed to parse birth data: dob={bool(dob_match)}, time={bool(time_match)}, lat={bool(lat_match)}, lng={bool(lng_match)}")
        return None
    
    result = {
        "dob": dob_match.group(1),
        "time": time_match.group(1),
        "lat": float(lat_match.group(1)),
        "lng": float(lng_match.group(1))
    }
    # Log only that parsing succeeded, not the actual sensitive data
    logger.info(f"Birth data parsed successfully")
    return result

def upsert_user(session, telegram_id: str):
    """Upsert user in database"""
    logger.debug(f"Upserting user with telegram_id={telegram_id}")
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            logger.debug(f"Updating existing user: {telegram_id}")
            user.last_seen = datetime.utcnow()
        else:
            logger.info(f"Creating new user: {telegram_id}")
            user = User(telegram_id=telegram_id)
            session.add(user)
        session.commit()
        logger.debug(f"User upserted successfully: {telegram_id}")
        return user
    except Exception as e:
        logger.exception(f"Error upserting user {telegram_id}: {e}")
        raise

def save_birth_data(session, telegram_id: str, birth_data: dict):
    """Save birth data to database"""
    # Log only that we're saving, not the actual sensitive data
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
            reading.delivered_at = datetime.utcnow()
            session.commit()
            logger.info(f"Reading {reading_id} marked as delivered")
        else:
            logger.warning(f"Reading {reading_id} not found for marking as delivered")
    except Exception as e:
        logger.exception(f"Error marking reading {reading_id} as delivered: {e}")
        raise

async def handle_telegram_update(update: dict):
    '''
    Entry point for Telegram webhook updates.
    Copilot agent should:
    - parse user message
    - validate input
    - call astrology.generate_natal_chart()
    - call llm.interpret_chart()
    - send reply to Telegram
    '''
    logger.info(f"=== Processing Telegram update ===")
    # Log only update type, not the full payload with sensitive data
    update_type = "message" if "message" in update else "other"
    logger.debug(f"Update type: {update_type}")
    
    try:
        # Extract message data
        if "message" not in update:
            logger.warning("Update does not contain a message, skipping")
            return {"ok": True}
        
        message = update["message"]
        
        # Validate message structure before extracting data
        if "chat" not in message or "id" not in message["chat"]:
            logger.error(f"Invalid message structure: missing chat.id. Message keys: {message.keys()}")
            return {"ok": True}
        
        if "from" not in message or "id" not in message["from"]:
            logger.error(f"Invalid message structure: missing from.id. Message keys: {message.keys()}")
            return {"ok": True}
        
        chat_id = message["chat"]["id"]
        telegram_id = str(message["from"]["id"])
        text = message.get("text", "")
        
        # Log detailed debug info to help diagnose issues
        logger.info(f"Processing message from chat_id={chat_id}, telegram_id={telegram_id}")
        logger.debug(f"Chat type: {message['chat'].get('type', 'unknown')}")
        logger.debug(f"Message ID: {message.get('message_id', 'unknown')}")
        # Log only message length, not the actual sensitive content
        logger.debug(f"Message length: {len(text)} characters")
        
        # Parse birth data
        birth_data = parse_birth_data(text)
        
        if not birth_data:
            logger.info(f"Invalid birth data format from telegram_id={telegram_id}")
            await send_telegram_message(chat_id, FORMAT_EXAMPLE)
            return {"ok": True}
        
        # Store user and birth data
        session = SessionLocal()
        birth_data_id = None
        try:
            logger.debug("Opening database session")
            upsert_user(session, telegram_id)
            birth_record = save_birth_data(session, telegram_id, birth_data)
            birth_data_id = birth_record.id
            logger.debug("Database operations completed successfully")
        except Exception as e:
            logger.exception(f"Database error for telegram_id={telegram_id}: {e}")
            await send_telegram_message(
                chat_id,
                "An error occurred while saving your data. Please try again later."
            )
            return {"ok": True}
        finally:
            session.close()
            logger.debug("Database session closed")
        
        # Generate natal chart
        try:
            logger.info(f"Generating natal chart for telegram_id={telegram_id}")
            chart = generate_natal_chart(
                birth_data["dob"],
                birth_data["time"],
                birth_data["lat"],
                birth_data["lng"]
            )
            logger.info(f"Natal chart generated successfully for telegram_id={telegram_id}")
        except Exception as e:
            logger.exception(f"Chart generation error for telegram_id={telegram_id}: {e}")
            await send_telegram_message(
                chat_id, 
                "Failed to generate natal chart. Please verify your birth date and time are correct."
            )
            return {"ok": True}
        
        # Get LLM interpretation
        try:
            logger.info(f"Getting LLM interpretation for telegram_id={telegram_id}")
            reading = interpret_chart(chart)
            logger.info(f"LLM interpretation completed for telegram_id={telegram_id}")
        except Exception as e:
            logger.exception(f"LLM interpretation error for telegram_id={telegram_id}: {e}")
            await send_telegram_message(
                chat_id,
                "Unable to generate your astrological reading at this time. Please try again later."
            )
            return {"ok": True}
        
        # Save reading to database before attempting to send
        session = SessionLocal()
        reading_id = None
        try:
            logger.debug("Opening database session to save reading")
            reading_record = save_reading(session, telegram_id, reading, birth_data_id)
            reading_id = reading_record.id
            logger.debug(f"Reading saved with id={reading_id}")
        except Exception as e:
            logger.exception(f"Error saving reading for telegram_id={telegram_id}: {e}")
            # Continue to try sending even if saving fails
        finally:
            session.close()
            logger.debug("Database session closed")
        
        # Send reading to user
        try:
            logger.info(f"Sending reading to telegram_id={telegram_id}")
            response = await send_telegram_message(chat_id, reading)
            
            # Check if message was delivered successfully
            if response is not None and reading_id is not None:
                # Message was sent successfully, mark as delivered
                session = SessionLocal()
                try:
                    mark_reading_delivered(session, reading_id)
                except Exception as e:
                    logger.exception(f"Error marking reading as delivered: {e}")
                finally:
                    session.close()
            elif response is None:
                # Message was not delivered (404 or other non-success)
                logger.warning(f"Reading saved but not delivered to telegram_id={telegram_id}. User can retrieve it later.")
            
            logger.info(f"=== Update processed successfully for telegram_id={telegram_id} ===")
        except Exception as e:
            logger.exception(f"Failed to send reading to telegram_id={telegram_id}: {e}")
            # Reading is saved in database, so it's not lost
            logger.info(f"Reading saved in database (id={reading_id}) but delivery failed for telegram_id={telegram_id}")
        
        # Always return ok: True to Telegram to acknowledge webhook receipt
        # This prevents Telegram from retrying the webhook repeatedly
        return {"ok": True}
        
    except Exception as e:
        # Log error but return ok to Telegram
        logger.exception(f"Critical error handling update: {e}")
        return {"ok": True}
