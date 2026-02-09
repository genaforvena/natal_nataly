import os
from fastapi import FastAPI, Request
from bot import handle_telegram_update
from db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    return await handle_telegram_update(data)
