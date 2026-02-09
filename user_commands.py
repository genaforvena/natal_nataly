"""
User Commands Module
Implements user-facing transparency and data audit commands.
"""
import json
import logging
from datetime import datetime
from db import SessionLocal
from models import User, Reading, AstroProfile, NatalChart, PipelineLog, UserNatalChart
from models import STATE_AWAITING_BIRTH_DATA, STATE_AWAITING_CONFIRMATION, STATE_AWAITING_EDIT_CONFIRMATION

# Configure logging
logger = logging.getLogger(__name__)


async def handle_my_data_command(telegram_id: str, send_message_func) -> bool:
    """
    Handle /my_data command - Show user their birth data.
    
    Args:
        telegram_id: User's Telegram ID
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was handled successfully
    """
    logger.info(f"[USER_CMD] /my_data requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if not user:
                await send_message_func("У тебя пока нет профиля. Отправь данные рождения, чтобы создать профиль.")
                return True
            
            # Get active profile
            profile = None
            if user.active_profile_id:
                profile = session.query(AstroProfile).filter_by(id=user.active_profile_id).first()
            
            if not profile:
                await send_message_func("У тебя пока нет активного профиля. Отправь данные рождения, чтобы создать профиль.")
                return True
            
            # Get normalized birth data from latest pipeline log
            pipeline_log = session.query(PipelineLog).filter_by(
                telegram_id=telegram_id
            ).order_by(PipelineLog.timestamp.desc()).first()
            
            # Parse birth data
            birth_data = json.loads(profile.birth_data_json)
            
            # Build response with normalized data if available
            response = "📊 **Your Birth Data**\n\n"
            
            response += f"**Date (local):** {birth_data.get('dob', 'N/A')}\n"
            response += f"**Time (local):** {birth_data.get('time', 'N/A')}\n"
            response += f"**Latitude:** {birth_data.get('lat', 'N/A')}\n"
            response += f"**Longitude:** {birth_data.get('lng', 'N/A')}\n"
            
            # Add timezone information if available from pipeline log
            if pipeline_log and pipeline_log.normalized_birth_data_json:
                normalized_data = json.loads(pipeline_log.normalized_birth_data_json)
                
                if normalized_data.get('timezone'):
                    response += f"\n**Timezone:** {normalized_data['timezone']}\n"
                    response += f"**Timezone Source:** {normalized_data.get('timezone_source', 'N/A')}\n"
                
                if pipeline_log.birth_datetime_local:
                    response += f"**Local DateTime:** {pipeline_log.birth_datetime_local.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                if pipeline_log.birth_datetime_utc:
                    response += f"**UTC DateTime:** {pipeline_log.birth_datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                
                if normalized_data.get('coordinates_source'):
                    response += f"**Coordinates Source:** {normalized_data['coordinates_source']}\n"
            
            # Add chart status
            natal_chart = session.query(NatalChart).filter_by(
                telegram_id=telegram_id
            ).order_by(NatalChart.created_at.desc()).first()
            
            if natal_chart:
                response += f"\n**Natal Chart Status:**\n"
                response += f"✅ Chart generated\n"
                if natal_chart.engine_version:
                    response += f"**Engine version:** {natal_chart.engine_version}\n"
                response += f"**Created at:** {natal_chart.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            else:
                response += f"\n**Natal Chart Status:**\n"
                response += f"❌ No chart generated yet\n"
            
            await send_message_func(response)
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        logger.exception(f"Error handling /my_data command: {e}")
        await send_message_func("Произошла ошибка при получении данных.")
        return True


async def handle_my_chart_raw_command(telegram_id: str, send_message_func) -> bool:
    """
    Handle /my_chart_raw command - Return raw natal chart data.
    
    Args:
        telegram_id: User's Telegram ID
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was handled successfully
    """
    logger.info(f"[USER_CMD] /my_chart_raw requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            # Get active user chart from unified table
            user_chart = session.query(UserNatalChart).filter_by(
                telegram_id=telegram_id,
                is_active=True
            ).order_by(UserNatalChart.created_at.desc()).first()
            
            if not user_chart:
                # Fallback to legacy NatalChart table
                natal_chart = session.query(NatalChart).filter_by(
                    telegram_id=telegram_id
                ).order_by(NatalChart.created_at.desc()).first()
                
                if not natal_chart:
                    await send_message_func("У тебя пока нет натальной карты. Отправь данные рождения или используй /upload_chart.")
                    return True
                
                # Parse legacy chart JSON
                chart_data = json.loads(natal_chart.natal_chart_json)
            else:
                # Parse unified chart JSON
                chart_data = json.loads(user_chart.chart_json)
            
            # Format as pretty JSON
            chart_json = json.dumps(chart_data, indent=2, ensure_ascii=False)
            
            # Check if message is too long for Telegram (max 4096 characters)
            if len(chart_json) > 3800:  # Leave room for formatting
                # Split into chunks
                response = "🔮 **Your Natal Chart (Raw Data)**\n\n"
                response += "⚠️ Chart data is too long, showing summary:\n\n"
                
                # Show planets only
                if "planets" in chart_data:
                    response += "**Planets:**\n```json\n"
                    response += json.dumps(chart_data["planets"], indent=2, ensure_ascii=False)
                    response += "\n```\n\n"
                
                response += "Use /my_chart_raw_full to download complete chart as file."
                await send_message_func(response)
            else:
                response = "🔮 **Your Natal Chart (Raw Data)**\n\n"
                response += "```json\n"
                response += chart_json
                response += "\n```\n\n"
                
                # Show source info
                if user_chart:
                    response += f"📊 **Source:** {user_chart.source}\n"
                    response += f"🔧 **Engine:** {user_chart.engine_version}\n"
                    response += f"📅 **Created:** {user_chart.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                
                response += "ℹ️ You can verify this chart on AstroSeek or other astrology services."
                await send_message_func(response)
            
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        logger.exception(f"Error handling /my_chart_raw command: {e}")
        await send_message_func("Произошла ошибка при получении карты.")
        return True


async def handle_my_readings_command(telegram_id: str, send_message_func, reading_id: str = None) -> bool:
    """
    Handle /my_readings command - List all user readings or retrieve specific reading.
    
    Args:
        telegram_id: User's Telegram ID
        send_message_func: Async function to send messages
        reading_id: Optional reading ID to retrieve specific reading
        
    Returns:
        bool: True if command was handled successfully
    """
    logger.info(f"[USER_CMD] /my_readings requested by {telegram_id}, reading_id={reading_id}")
    
    try:
        session = SessionLocal()
        try:
            if reading_id:
                # Retrieve specific reading
                try:
                    reading_id_int = int(reading_id)
                    reading = session.query(Reading).filter_by(
                        id=reading_id_int,
                        telegram_id=telegram_id
                    ).first()
                    
                    if not reading:
                        await send_message_func(f"Reading #{reading_id} не найден или не принадлежит тебе.")
                        return True
                    
                    # Send reading
                    response = f"📖 **Reading #{reading.id}**\n\n"
                    response += f"**Created:** {reading.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    if reading.model_used:
                        response += f"**Model:** {reading.model_used}\n"
                    if reading.prompt_name:
                        response += f"**Prompt:** {reading.prompt_name}\n"
                    response += f"\n{reading.reading_text}\n"
                    
                    await send_message_func(response)
                    return True
                    
                except ValueError:
                    await send_message_func(f"Неверный ID reading: {reading_id}")
                    return True
            
            # List all readings
            readings = session.query(Reading).filter_by(
                telegram_id=telegram_id
            ).order_by(Reading.created_at.desc()).all()
            
            if not readings:
                await send_message_func("У тебя пока нет сохранённых readings. Сгенерируй натальную карту, чтобы получить первое reading.")
                return True
            
            # Build readings list
            response = "📚 **Your Readings**\n\n"
            
            for reading in readings[:20]:  # Limit to 20 most recent
                status = "✅" if reading.delivered else "⏳"
                response += f"{status} **#{reading.id}** - {reading.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                if reading.model_used:
                    response += f"   Model: {reading.model_used}\n"
                if reading.prompt_name:
                    response += f"   Prompt: {reading.prompt_name}\n"
                response += "\n"
            
            if len(readings) > 20:
                response += f"\n... and {len(readings) - 20} more readings\n"
            
            response += "\nℹ️ To retrieve a specific reading, use: /my_readings <id>\n"
            response += "Example: /my_readings 5"
            
            await send_message_func(response)
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        logger.exception(f"Error handling /my_readings command: {e}")
        await send_message_func("Произошла ошибка при получении readings.")
        return True


async def handle_edit_birth_command(telegram_id: str, send_message_func) -> bool:
    """
    Handle /edit_birth command - Start flow to edit birth data.
    
    Args:
        telegram_id: User's Telegram ID
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was handled successfully
    """
    logger.info(f"[USER_CMD] /edit_birth requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if not user:
                await send_message_func("У тебя пока нет профиля.")
                return True
            
            # Get active profile
            profile = None
            if user.active_profile_id:
                profile = session.query(AstroProfile).filter_by(id=user.active_profile_id).first()
            
            if not profile:
                await send_message_func("У тебя пока нет активного профиля с данными для редактирования.")
                return True
            
            # Show current data
            birth_data = json.loads(profile.birth_data_json)
            
            response = "✏️ **Edit Birth Data**\n\n"
            response += "**Current data:**\n"
            response += f"Date: {birth_data.get('dob', 'N/A')}\n"
            response += f"Time: {birth_data.get('time', 'N/A')}\n"
            response += f"Latitude: {birth_data.get('lat', 'N/A')}\n"
            response += f"Longitude: {birth_data.get('lng', 'N/A')}\n\n"
            response += "Please send new birth data in the same format as before:\n"
            response += "DOB: YYYY-MM-DD\n"
            response += "Time: HH:MM\n"
            response += "Lat: XX.XXXX\n"
            response += "Lng: XX.XXXX"
            
            await send_message_func(response)
            
            # Update user state to awaiting_birth_data
            user.state = STATE_AWAITING_BIRTH_DATA
            session.commit()
            
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        logger.exception(f"Error handling /edit_birth command: {e}")
        await send_message_func("Произошла ошибка при редактировании данных.")
        return True


async def handle_user_command(telegram_id: str, command: str, send_message_func) -> bool:
    """
    Handle user transparency commands. Returns True if command was handled.
    
    Args:
        telegram_id: User's Telegram ID
        command: Command string (e.g., "/my_data")
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was a user command and was handled
    """
    # Parse command and arguments
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None
    
    if cmd == "/my_data":
        return await handle_my_data_command(telegram_id, send_message_func)
    elif cmd == "/my_chart_raw":
        return await handle_my_chart_raw_command(telegram_id, send_message_func)
    elif cmd == "/my_readings":
        return await handle_my_readings_command(telegram_id, send_message_func, arg)
    elif cmd == "/edit_birth":
        return await handle_edit_birth_command(telegram_id, send_message_func)
    elif cmd == "/upload_chart":
        return await handle_upload_chart_command(telegram_id, send_message_func)
    
    return False


async def handle_upload_chart_command(telegram_id: str, send_message_func) -> bool:
    """
    Handle /upload_chart command - Start flow to upload a chart.
    
    Args:
        telegram_id: User's Telegram ID
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was handled successfully
    """
    logger.info(f"[USER_CMD] /upload_chart requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if not user:
                # Create user if doesn't exist
                user = User(telegram_id=telegram_id)
                session.add(user)
            
            # Set user state to awaiting chart upload
            user.state = "awaiting_chart_upload"
            session.commit()
            
            response = "📤 **Upload Your Natal Chart**\n\n"
            response += "Please send your natal chart data in text format.\n\n"
            response += "**Supported format (AstroSeek style):**\n"
            response += "```\n"
            response += "Sun: 10°30' Capricorn, House 4\n"
            response += "Moon: 10°10' Libra, House 1\n"
            response += "Mercury: 5°45' Capricorn, House 4\n"
            response += "Venus: 15°48' Capricorn, House 4\n"
            response += "...\n\n"
            response += "House 1: 26°30' Virgo\n"
            response += "House 2: 22°15' Libra\n"
            response += "...\n\n"
            response += "Sun Square Moon (orb: 0.03)\n"
            response += "Sun Conjunction Venus (orb: 5.42)\n"
            response += "...\n"
            response += "```\n\n"
            response += "ℹ️ Send your chart text and I'll parse it for you.\n"
            response += "Type /cancel to cancel upload."
            
            await send_message_func(response)
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        logger.exception(f"Error handling /upload_chart command: {e}")
        await send_message_func("Произошла ошибка при загрузке карты.")
        return True
