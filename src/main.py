import os
import logging
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from src.bot import handle_telegram_update
from src.db import init_db, SessionLocal
from src.message_cache import mark_if_new, should_debounce, update_message_analytics, mark_all_pending_as_replied
from src.models import ProcessedMessage


class HealthCheckFilter(logging.Filter):
    """Filter out health check endpoint logs to reduce noise."""
    def filter(self, record: logging.LogRecord) -> bool:
        # Filter out uvicorn access logs for GET/HEAD requests to /health endpoint
        # This matches the exact pattern: "GET /health HTTP" or "HEAD /health HTTP"
        message = record.getMessage()
        return not ('GET /health HTTP' in message or 'HEAD /health HTTP' in message)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Set specific log levels for different modules
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce httpx noise
logging.getLogger("httpcore").setLevel(logging.WARNING)  # Reduce httpcore noise

# Add filter to uvicorn access logger to suppress health check logs
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("=== Application starting up ===")
    
    # Log running mode
    render_mode = os.getenv("RENDER", "false").lower() == "true"
    mode = "render" if render_mode else "local"
    logger.info(f"Running mode: {mode}")
    
    # Log webhook status
    webhook_enabled = bool(os.getenv("WEBHOOK_URL")) and render_mode
    logger.info(f"Webhook enabled: {webhook_enabled}")
    if webhook_enabled:
        logger.info(f"Webhook URL: {os.getenv('WEBHOOK_URL')}")
    
    # Initialize database (synchronous call)
    init_db()
    logger.info("Database initialized")
    
    # Clean up stale pending messages from before restart
    # These messages are from before app restart and won't be processed
    # Mark them as replied to prevent blocking new messages
    try:
        session = SessionLocal()
        try:
            stale_messages = session.query(ProcessedMessage).filter_by(
                reply_sent=False
            ).all()
            
            if stale_messages:
                # Group by user to log per-user counts
                user_counts = {}
                for msg in stale_messages:
                    user_counts[msg.telegram_id] = user_counts.get(msg.telegram_id, 0) + 1
                
                logger.warning(
                    f"Found {len(stale_messages)} stale pending message(s) from before restart "
                    f"for {len(user_counts)} user(s). Marking as replied to unblock processing."
                )
                
                for user_id, count in user_counts.items():
                    logger.info(f"  User {user_id}: {count} stale message(s)")
                
                # Mark all as replied using bulk update for efficiency
                now = datetime.now(timezone.utc)
                session.query(ProcessedMessage).filter_by(
                    reply_sent=False
                ).update({
                    'reply_sent': True,
                    'reply_sent_at': now
                })
                session.commit()
                logger.info(f"Marked {len(stale_messages)} stale message(s) as replied")
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"Error cleaning up stale messages: {e}")
    
    logger.info("=== Application startup complete ===")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    logger.info("Webhook endpoint called")
    try:
        # Verify Telegram secret token if configured (security feature)
        secret_token = os.getenv("TELEGRAM_SECRET_TOKEN")
        if secret_token:
            received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not received_token or received_token != secret_token:
                logger.warning("Webhook request rejected: invalid or missing secret token")
                return {"ok": False, "error": "Unauthorized"}
        
        data = await request.json()
        # Extract message metadata safely
        message = data.get("message", {})
        message_id = message.get("message_id")
        chat_id = message.get("chat", {}).get("id", "unknown")
        telegram_id = message.get("from", {}).get("id")
        message_text = message.get("text", "")
        
        logger.debug(f"Webhook received: message_id={message_id}, chat_id={chat_id}, telegram_id={telegram_id}")
        
        # Dedup + debounce – only when we have valid IDs
        if message_id is not None and telegram_id is not None:
            telegram_id_str = str(telegram_id)

            # 1. Atomically mark message in DB (prevents duplicates across restarts)
            is_new = mark_if_new(telegram_id_str, message_id, message_text)
            if not is_new:
                logger.info(f"Skipping duplicate message {message_id} from user {telegram_id_str}")
                return {"ok": True, "skipped": "duplicate"}

            # 2. In-memory debounce: throttle rapid successive messages from same user
            if should_debounce(telegram_id_str):
                logger.info(
                    f"Message {message_id} from user {telegram_id_str} debounced (throttled)"
                )
                return {"ok": True, "throttled": True}

        # Process message and track latency for analytics
        start_time = time.monotonic()
        result = await handle_telegram_update(data)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Record analytics (best-effort, non-blocking)
        if message_id is not None and telegram_id is not None:
            try:
                update_message_analytics(str(telegram_id), message_id, latency_ms, role="user")
            except Exception as analytics_err:
                logger.debug("Analytics update failed (non-critical): %s", analytics_err)

        logger.debug(f"Webhook processing result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Return generic error to client, detailed error is in logs
        return {"ok": False, "error": "Internal server error"}
