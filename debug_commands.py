"""
Debug Commands Module
Implements developer-only commands for debugging and inspection.
"""
import os
import json
import logging
from typing import Optional
from datetime import datetime
from db import SessionLocal
from models import PipelineLog, NatalChart, DebugSession, User, Reading
from debug import is_developer, DEBUG_MODE

# Configure logging
logger = logging.getLogger(__name__)


async def handle_debug_command(telegram_id: str, command: str, send_message_func) -> bool:
    """
    Handle debug commands. Returns True if command was handled.
    
    Args:
        telegram_id: User's Telegram ID
        command: Command string (e.g., "/debug_birth")
        send_message_func: Async function to send messages
        
    Returns:
        bool: True if command was a debug command (handled or rejected)
    """
    # Check if this is a debug command
    if not command.startswith("/debug_") and command != "/show_chart":
        return False
    
    # Verify developer access
    if not is_developer(telegram_id):
        await send_message_func(
            "⛔ Debug commands are only available to the developer."
        )
        return True
    
    # Route to appropriate handler
    if command == "/debug_birth":
        await handle_debug_birth(telegram_id, send_message_func)
    elif command == "/debug_chart":
        await handle_debug_chart(telegram_id, send_message_func)
    elif command == "/debug_pipeline":
        await handle_debug_pipeline(telegram_id, send_message_func)
    elif command == "/show_chart":
        await handle_show_chart(telegram_id, send_message_func)
    else:
        await send_message_func(
            f"Unknown debug command: {command}\n\n"
            "Available commands:\n"
            "/debug_birth - Show parsed and normalized birth data\n"
            "/debug_chart - Show natal chart JSON\n"
            "/debug_pipeline - Show complete pipeline trace\n"
            "/show_chart - Show chart visualization (SVG)"
        )
    
    return True


async def handle_debug_birth(telegram_id: str, send_message_func):
    """
    /debug_birth command - Shows parsed and normalized birth data
    """
    logger.info(f"[DEBUG_CMD] /debug_birth requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            # Get latest pipeline log
            pipeline_log = session.query(PipelineLog).filter_by(
                telegram_id=telegram_id
            ).order_by(PipelineLog.timestamp.desc()).first()
            
            if not pipeline_log:
                await send_message_func(
                    "🔍 No debug data found. Generate a natal chart first."
                )
                return
            
            # Parse JSON data
            parsed_data = (
                json.loads(pipeline_log.parsed_birth_data_json)
                if pipeline_log.parsed_birth_data_json else None
            )
            normalized_data = (
                json.loads(pipeline_log.normalized_birth_data_json)
                if pipeline_log.normalized_birth_data_json else None
            )
            
            # Build response
            response = "🔍 **DEBUG: Birth Data**\n\n"
            response += f"📝 **Session ID:** `{pipeline_log.session_id}`\n"
            response += f"⏰ **Timestamp:** {pipeline_log.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            
            if parsed_data:
                response += "**📋 Parsed Data (LLM Output):**\n```json\n"
                response += json.dumps(parsed_data, indent=2, ensure_ascii=False)
                response += "\n```\n\n"
            
            if normalized_data:
                response += "**✅ Normalized Data (System Validated):**\n```json\n"
                response += json.dumps(normalized_data, indent=2, ensure_ascii=False)
                response += "\n```\n\n"
            
            # Timezone info
            if pipeline_log.timezone:
                response += f"🌍 **Timezone:** {pipeline_log.timezone}\n"
                response += f"📍 **Timezone Source:** {pipeline_log.timezone_source}\n"
                response += f"✔️ **Validation Status:** {pipeline_log.timezone_validation_status}\n\n"
            
            # UTC/Local times
            if pipeline_log.birth_datetime_utc:
                response += f"🕐 **UTC Time:** {pipeline_log.birth_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if pipeline_log.birth_datetime_local:
                response += f"🕑 **Local Time:** {pipeline_log.birth_datetime_local.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Coordinates
            if normalized_data and 'lat' in normalized_data and 'lng' in normalized_data:
                response += f"📍 **Coordinates:** {normalized_data['lat']}, {normalized_data['lng']}\n"
                response += f"📍 **Coordinates Source:** {pipeline_log.coordinates_source or 'N/A'}\n"
            
            await send_message_func(response)
            
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Error handling /debug_birth: {e}")
        await send_message_func(f"❌ Error retrieving debug data: {str(e)}")


async def handle_debug_chart(telegram_id: str, send_message_func):
    """
    /debug_chart command - Shows natal chart JSON
    """
    logger.info(f"[DEBUG_CMD] /debug_chart requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            # Get latest natal chart
            chart_record = session.query(NatalChart).filter_by(
                telegram_id=telegram_id
            ).order_by(NatalChart.created_at.desc()).first()
            
            if not chart_record:
                await send_message_func(
                    "🔍 No natal chart found. Generate a chart first."
                )
                return
            
            # Parse chart JSON
            chart_data = json.loads(chart_record.natal_chart_json)
            birth_data = json.loads(chart_record.birth_data_json)
            
            # Build response
            response = "🔮 **DEBUG: Natal Chart**\n\n"
            response += f"🆔 **Chart ID:** {chart_record.id}\n"
            response += f"⏰ **Created:** {chart_record.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            response += f"🔧 **Engine Version:** {chart_record.engine_version}\n"
            response += f"📚 **Ephemeris Version:** {chart_record.ephemeris_version}\n"
            response += f"#️⃣ **Chart Hash:** `{chart_record.chart_hash[:16]}...`\n\n"
            
            response += "**📊 Birth Data:**\n```json\n"
            response += json.dumps(birth_data, indent=2, ensure_ascii=False)
            response += "\n```\n\n"
            
            response += "**🌟 Natal Chart:**\n```json\n"
            chart_json_str = json.dumps(chart_data, indent=2, ensure_ascii=False)
            
            # Telegram has a 4096 character limit, so we might need to truncate
            if len(response) + len(chart_json_str) + 10 > 4000:
                chart_json_str = chart_json_str[:3500] + "\n... (truncated)"
            
            response += chart_json_str
            response += "\n```"
            
            # Check if response is too long for Telegram
            if len(response) > 4000:
                # Send truncated version with note
                response_truncated = response[:3900] + "\n... (truncated due to length)\n```\n\n"
                response_truncated += "💡 Tip: Use `/debug_pipeline` to see full session data."
                await send_message_func(response_truncated)
            else:
                await send_message_func(response)
            
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Error handling /debug_chart: {e}")
        await send_message_func(f"❌ Error retrieving chart data: {str(e)}")


async def handle_debug_pipeline(telegram_id: str, send_message_func):
    """
    /debug_pipeline command - Shows complete pipeline trace
    """
    logger.info(f"[DEBUG_CMD] /debug_pipeline requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            # Get latest debug session
            debug_session = session.query(DebugSession).filter_by(
                telegram_id=telegram_id
            ).order_by(DebugSession.started_at.desc()).first()
            
            if not debug_session:
                await send_message_func(
                    "🔍 No debug session found. Generate a chart first with DEBUG_MODE enabled."
                )
                return
            
            # Get related records
            pipeline_log = None
            if debug_session.pipeline_log_id:
                pipeline_log = session.query(PipelineLog).filter_by(
                    id=debug_session.pipeline_log_id
                ).first()
            
            # Build response
            response = "🔍 **DEBUG: Complete Pipeline Trace**\n\n"
            response += f"🆔 **Session ID:** `{debug_session.session_id}`\n"
            response += f"⏰ **Started:** {debug_session.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            
            if debug_session.completed_at:
                response += f"✅ **Completed:** {debug_session.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            
            response += f"📊 **Status:** {debug_session.status}\n\n"
            
            if pipeline_log:
                response += "**Pipeline Stages:**\n\n"
                
                # Stage 1: Raw Input
                response += "1️⃣ **Raw Input**\n"
                if pipeline_log.raw_user_message:
                    msg_preview = pipeline_log.raw_user_message[:100]
                    response += f"   📝 Message: `{msg_preview}...`\n"
                response += f"   ⏰ Time: {pipeline_log.timestamp.strftime('%H:%M:%S')}\n\n"
                
                # Stage 2: Parsed Data
                if pipeline_log.parsed_birth_data_json:
                    response += "2️⃣ **LLM Parse** ✅\n"
                    parsed = json.loads(pipeline_log.parsed_birth_data_json)
                    if 'confidence' in parsed:
                        response += f"   📊 Confidence: {parsed['confidence']}\n"
                    response += "\n"
                
                # Stage 3: Normalized Data
                if pipeline_log.normalized_birth_data_json:
                    response += "3️⃣ **Normalization** ✅\n"
                    response += f"   🌍 Timezone: {pipeline_log.timezone or 'N/A'}\n"
                    response += f"   ✔️ TZ Status: {pipeline_log.timezone_validation_status or 'N/A'}\n\n"
                
                # Stage 4: Chart Generated
                if debug_session.natal_chart_id:
                    response += "4️⃣ **Chart Generated** ✅\n"
                    response += f"   🆔 Chart ID: {debug_session.natal_chart_id}\n\n"
                
                # Stage 5: Reading Sent
                if debug_session.reading_id:
                    response += "5️⃣ **Reading Sent** ✅\n"
                    response += f"   🆔 Reading ID: {debug_session.reading_id}\n\n"
                    
                    # Get reading details
                    reading = session.query(Reading).filter_by(
                        id=debug_session.reading_id
                    ).first()
                    
                    if reading:
                        response += "**LLM Prompt Info:**\n"
                        response += f"   📋 Prompt: {reading.prompt_name or 'N/A'}\n"
                        response += f"   #️⃣ Hash: `{reading.prompt_hash or 'N/A'}`\n"
                        response += f"   🤖 Model: {reading.model_used or 'N/A'}\n"
                
                # Error info
                if pipeline_log.error_message:
                    response += f"\n❌ **Error:** {pipeline_log.error_message}\n"
            
            await send_message_func(response)
            
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Error handling /debug_pipeline: {e}")
        await send_message_func(f"❌ Error retrieving pipeline data: {str(e)}")


async def handle_show_chart(telegram_id: str, send_message_func):
    """
    /show_chart command - Shows chart visualization (SVG)
    """
    logger.info(f"[DEBUG_CMD] /show_chart requested by {telegram_id}")
    
    try:
        session = SessionLocal()
        try:
            # Get latest natal chart
            chart_record = session.query(NatalChart).filter_by(
                telegram_id=telegram_id
            ).order_by(NatalChart.created_at.desc()).first()
            
            if not chart_record:
                await send_message_func(
                    "🔍 No natal chart found. Generate a chart first."
                )
                return
            
            # Parse chart data
            chart_data = json.loads(chart_record.natal_chart_json)
            
            # Generate SVG
            from chart_svg import save_chart_svg
            try:
                svg_path = save_chart_svg(telegram_id, chart_data)
                
                # For now, send a text representation
                # TODO: Send actual SVG file via Telegram
                response = "🔮 **Natal Chart Visualization**\n\n"
                response += f"✅ SVG chart generated and saved to: `{svg_path}`\n\n"
                response += "**Planetary Positions:**\n"
                
                for planet, data in chart_data.items():
                    if isinstance(data, dict) and 'sign' in data and 'degree' in data:
                        degree = data['degree'] % 30  # Degree within sign
                        response += f"• {planet}: {data['sign']} {degree:.2f}°\n"
                
                await send_message_func(response)
            except Exception as e:
                logger.exception(f"Error generating SVG: {e}")
                # Fallback to text representation
                response = "🔮 **Natal Chart Visualization**\n\n"
                response += "*(SVG generation failed, showing text format)*\n\n"
                response += "**Planetary Positions:**\n"
                
                for planet, data in chart_data.items():
                    if isinstance(data, dict) and 'sign' in data and 'degree' in data:
                        degree = data['degree'] % 30  # Degree within sign
                        response += f"• {planet}: {data['sign']} {degree:.2f}°\n"
                
                await send_message_func(response)
            
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Error handling /show_chart: {e}")
        await send_message_func(f"❌ Error generating chart visualization: {str(e)}")
