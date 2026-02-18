"""Webhook endpoint for Telegram bot integration with FastAPI."""

import logging

from fastapi import APIRouter, Request
from telegram import Update

logger = logging.getLogger(__name__)

router = APIRouter()

_bot_app = None


def set_bot_app(app):
    global _bot_app
    _bot_app = app


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram webhook updates."""
    if _bot_app is None:
        return {"error": "Bot not initialized"}

    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)
    await _bot_app.process_update(update)
    return {"ok": True}
