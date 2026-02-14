import os
import logging
from fastapi import FastAPI, Request
from src.bot import handle_telegram_update
from src.db import init_db
from src.message_cache import mark_if_new, has_pending_reply, mark_reply_sent


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
        
        # Check if this message has already been processed (atomic operation)
        # Only apply deduplication if we have valid IDs (not None)
        if message_id is not None and telegram_id is not None:
            telegram_id_str = str(telegram_id)
            
            # First, check if user has pending messages awaiting reply (throttling check)
            # We do this BEFORE marking as new to avoid race condition where the current
            # message gets counted as "pending" immediately after being added to DB
            if has_pending_reply(telegram_id_str):
                # User has pending messages, throttle this one
                # But still mark it in DB to prevent duplicate processing if retried
                is_new = mark_if_new(telegram_id_str, message_id)
                if is_new:
                    # Mark as "replied" to prevent this throttled message from blocking future messages.
                    # Note: This is semantically "message is complete/resolved" rather than "reply was sent"
                    # since throttled messages intentionally receive no reply.
                    mark_reply_sent(telegram_id_str, message_id)
                    logger.info(
                        f"Message {message_id} from user {telegram_id_str} throttled - "
                        f"user has pending messages awaiting reply"
                    )
                else:
                    logger.info(f"Duplicate throttled message {message_id} from user {telegram_id_str}")
                return {"ok": True, "throttled": True}
            
            # Now check if this specific message is a duplicate
            is_new = mark_if_new(telegram_id_str, message_id)
            
            if not is_new:
                logger.info(f"Skipping duplicate message {message_id} from user {telegram_id_str}")
                return {"ok": True, "skipped": "duplicate"}
        
        result = await handle_telegram_update(data)
        logger.debug(f"Webhook processing result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Return generic error to client, detailed error is in logs
        return {"ok": False, "error": "Internal server error"}
