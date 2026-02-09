import os
from astrology import generate_natal_chart
from llm import interpret_chart

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
    return {"ok": True}
