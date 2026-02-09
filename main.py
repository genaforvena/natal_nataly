import os
import logging
from fastapi import FastAPI, Request
from bot import handle_telegram_update
from db import init_db

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

logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("=== Application starting up ===")
    init_db()
    logger.info("Database initialized")
    logger.info("=== Application startup complete ===")

@app.get("/health")
async def health():
    logger.debug("Health check endpoint called")
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    logger.info("Webhook endpoint called")
    try:
        data = await request.json()
        logger.debug(f"Webhook received: {data}")
        result = await handle_telegram_update(data)
        logger.debug(f"Webhook processing result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return {"ok": False, "error": str(e)}
