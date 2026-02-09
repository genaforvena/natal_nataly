import os
import re
import httpx
import logging
from datetime import datetime
from astrology import generate_natal_chart
from llm import interpret_chart
from db import SessionLocal
from models import User, BirthData

# Configure logging
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

logger.info(f"Bot initialized with Telegram API URL configured")

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
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text
                }
            )
            # Check if the request was successful (2xx status codes)
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Message sent successfully to chat_id={chat_id}, status={response.status_code}")
                return response
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
    except Exception as e:
        logger.exception(f"Error saving birth data for {telegram_id}: {e}")
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
        chat_id = message["chat"]["id"]
        telegram_id = str(message["from"]["id"])
        text = message.get("text", "")
        
        logger.info(f"Processing message from chat_id={chat_id}, telegram_id={telegram_id}")
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
        try:
            logger.debug("Opening database session")
            upsert_user(session, telegram_id)
            save_birth_data(session, telegram_id, birth_data)
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
        
        # Send reading to user
        try:
            logger.info(f"Sending reading to telegram_id={telegram_id}")
            await send_telegram_message(chat_id, reading)
            logger.info(f"=== Update processed successfully for telegram_id={telegram_id} ===")
        except Exception as e:
            logger.exception(f"Failed to send reading to telegram_id={telegram_id}: {e}")
            # Cannot notify user since message sending failed
            # This is typically due to invalid bot token, chat_id, or Telegram API issues
        
        return {"ok": True}
        
    except Exception as e:
        # Log error but return ok to Telegram
        logger.exception(f"Critical error handling update: {e}")
        return {"ok": True}
