import os
import logging
from fastapi import FastAPI, Request
from src.bot import handle_telegram_update
from src.db import init_db
from src.services.analytics import analytics


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
        data = await request.json()

        # Track raw message event
        message = data.get("message", {})
        if message:
            telegram_id = str(message.get("from", {}).get("id", "unknown"))
            analytics.track_event(
                user_id=telegram_id,
                event_name="message_received",
                properties={
                    "chat_type": message.get("chat", {}).get("type"),
                    "has_text": bool(message.get("text")),
                    "has_document": bool(message.get("document")),
                    "has_photo": bool(message.get("photo"))
                }
            )

        # Log only non-sensitive metadata
        message_id = message.get("message_id", "unknown")
        chat_id = message.get("chat", {}).get("id", "unknown")
        logger.debug(f"Webhook received: message_id={message_id}, chat_id={chat_id}")
        result = await handle_telegram_update(data)
        logger.debug(f"Webhook processing result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Return generic error to client, detailed error is in logs
        return {"ok": False, "error": "Internal server error"}
