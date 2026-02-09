import os
import re
import httpx
from datetime import datetime
from astrology import generate_natal_chart
from llm import interpret_chart
from db import SessionLocal
from models import User, BirthData

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

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
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            }
        )

def parse_birth_data(text: str):
    """Parse birth data from user message"""
    dob_pattern = r"DOB:\s*(\d{4}-\d{2}-\d{2})"
    time_pattern = r"Time:\s*(\d{2}:\d{2})"
    lat_pattern = r"Lat:\s*([-]?\d+\.?\d*)"
    lng_pattern = r"Lng:\s*([-]?\d+\.?\d*)"
    
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    time_match = re.search(time_pattern, text, re.IGNORECASE)
    lat_match = re.search(lat_pattern, text, re.IGNORECASE)
    lng_match = re.search(lng_pattern, text, re.IGNORECASE)
    
    if not all([dob_match, time_match, lat_match, lng_match]):
        return None
    
    return {
        "dob": dob_match.group(1),
        "time": time_match.group(1),
        "lat": float(lat_match.group(1)),
        "lng": float(lng_match.group(1))
    }

def upsert_user(session, telegram_id: str):
    """Upsert user in database"""
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.last_seen = datetime.utcnow()
    else:
        user = User(telegram_id=telegram_id)
        session.add(user)
    session.commit()
    return user

def save_birth_data(session, telegram_id: str, birth_data: dict):
    """Save birth data to database"""
    birth_record = BirthData(
        telegram_id=telegram_id,
        dob=birth_data["dob"],
        time=birth_data["time"],
        lat=birth_data["lat"],
        lng=birth_data["lng"]
    )
    session.add(birth_record)
    session.commit()

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
    try:
        # Extract message data
        if "message" not in update:
            return {"ok": True}
        
        message = update["message"]
        chat_id = message["chat"]["id"]
        telegram_id = str(message["from"]["id"])
        text = message.get("text", "")
        
        # Parse birth data
        birth_data = parse_birth_data(text)
        
        if not birth_data:
            await send_telegram_message(chat_id, FORMAT_EXAMPLE)
            return {"ok": True}
        
        # Store user and birth data
        session = SessionLocal()
        try:
            upsert_user(session, telegram_id)
            save_birth_data(session, telegram_id, birth_data)
        finally:
            session.close()
        
        # Generate natal chart
        try:
            chart = generate_natal_chart(
                birth_data["dob"],
                birth_data["time"],
                birth_data["lat"],
                birth_data["lng"]
            )
        except Exception as e:
            print(f"Chart generation error: {e}")
            await send_telegram_message(
                chat_id, 
                "Failed to generate natal chart. Please verify your birth date and time are correct."
            )
            return {"ok": True}
        
        # Get LLM interpretation
        try:
            reading = interpret_chart(chart)
        except Exception as e:
            print(f"LLM interpretation error: {e}")
            await send_telegram_message(
                chat_id,
                "Unable to generate your astrological reading at this time. Please try again later."
            )
            return {"ok": True}
        
        # Send reading to user
        await send_telegram_message(chat_id, reading)
        
        return {"ok": True}
        
    except Exception as e:
        # Log error but return ok to Telegram
        print(f"Error handling update: {e}")
        return {"ok": True}
