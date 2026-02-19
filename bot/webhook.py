"""Webhook endpoint for Telegram bot integration with FastAPI."""

import logging

from fastapi import APIRouter, Request
from telegram import Update

logger = logging.getLogger(__name__)

router = APIRouter()

_bot_app = None
_webhook_secret: str = ""


def set_bot_app(app):
    global _bot_app
    _bot_app = app


def set_webhook_secret(secret: str):
    global _webhook_secret
    _webhook_secret = secret


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram webhook updates."""
    if _bot_app is None:
        return {"error": "Bot not initialized"}

    # Verify webhook secret token
    if _webhook_secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != _webhook_secret:
            logger.warning("Webhook request with invalid secret token")
            return {"error": "Unauthorized"}

    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)
    await _bot_app.process_update(update)
    return {"ok": True}
