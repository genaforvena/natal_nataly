import os
import json
import httpx
import logging
from datetime import datetime, timezone
from astrology import generate_natal_chart
from llm import extract_birth_data, generate_clarification_question, interpret_chart
from db import SessionLocal
from models import User, BirthData, Reading
from models import STATE_AWAITING_BIRTH_DATA, STATE_AWAITING_CLARIFICATION, STATE_HAS_CHART, STATE_CHATTING_ABOUT_CHART

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


async def handle_awaiting_birth_data(session, user: User, chat_id: int, text: str):
    """Handle messages when user is in awaiting_birth_data state"""
    logger.info(f"Handling awaiting_birth_data for user {user.telegram_id}")
    
    try:
        # Use LLM to extract birth data from free-form text
        birth_data = extract_birth_data(text)
        
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
            await send_telegram_message(
                chat_id,
                "Пожалуйста, укажите дату рождения (YYYY-MM-DD), время (HH:MM) и место (город или координаты)."
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
        
        # Save birth data
        birth_record = save_birth_data(session, user.telegram_id, birth_data)
        
        # Store natal chart and update state
        chart_json = json.dumps(chart)
        update_user_state(session, user.telegram_id, STATE_HAS_CHART, natal_chart_json=chart_json)
        
        # Send confirmation message
        await send_telegram_message(
            chat_id,
            "✨ Натальная карта готова.\nТеперь ты можешь задавать любые вопросы о себе."
        )
        
        logger.info(f"Birth data processed successfully for user {user.telegram_id}")
        
    except Exception as e:
        logger.exception(f"Error handling awaiting_birth_data: {e}")
        await send_telegram_message(
            chat_id,
            "Произошла ошибка при обработке данных. Пожалуйста, попробуйте ещё раз."
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
        
        # Save birth data
        birth_record = save_birth_data(session, user.telegram_id, birth_data)
        
        # Store natal chart and update state
        chart_json = json.dumps(chart)
        update_user_state(session, user.telegram_id, STATE_HAS_CHART, natal_chart_json=chart_json, missing_fields=None)
        
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
        # Load natal chart from database
        if not user.natal_chart_json:
            logger.error(f"User {user.telegram_id} in chatting state but no chart found")
            await send_telegram_message(
                chat_id,
                "Кажется, у меня нет твоей натальной карты. Пожалуйста, предоставь данные рождения снова."
            )
            update_user_state(session, user.telegram_id, STATE_AWAITING_BIRTH_DATA)
            return
        
        chart = json.loads(user.natal_chart_json)
        
        # Update state to chatting_about_chart if it was has_chart
        if user.state == STATE_HAS_CHART:
            update_user_state(session, user.telegram_id, STATE_CHATTING_ABOUT_CHART)
        
        # Get LLM interpretation based on user's question
        logger.info(f"Getting chart interpretation for user question")
        reading = interpret_chart(chart, question=text)
        
        # Save reading to database
        reading_record = save_reading(session, user.telegram_id, reading)
        reading_id = reading_record.id
        
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


async def route_message(session, user: User, chat_id: int, text: str):
    """Route message based on user state"""
    logger.info(f"Routing message for user {user.telegram_id}, state={user.state}")
    
    if user.state == STATE_AWAITING_BIRTH_DATA:
        await handle_awaiting_birth_data(session, user, chat_id, text)
    elif user.state == STATE_AWAITING_CLARIFICATION:
        await handle_awaiting_clarification(session, user, chat_id, text)
    elif user.state in [STATE_HAS_CHART, STATE_CHATTING_ABOUT_CHART]:
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
            
            # Route message based on state
            await route_message(session, user, chat_id, text)
            
            logger.info(f"=== Update processed successfully for telegram_id={telegram_id} ===")
        finally:
            session.close()
        
        return {"ok": True}
        
    except Exception as e:
        logger.exception(f"Critical error handling update: {e}")
        return {"ok": True}
