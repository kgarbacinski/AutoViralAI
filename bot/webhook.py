import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from telegram import Update

from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

_bot_app = None
_webhook_secret: str = ""

MAX_WEBHOOK_BODY_SIZE = 1_000_000


def set_bot_app(app: object) -> None:
    global _bot_app
    _bot_app = app


def set_webhook_secret(secret: str) -> None:
    global _webhook_secret
    _webhook_secret = secret


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    if _bot_app is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    if _webhook_secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(token, _webhook_secret):
            logger.warning("Webhook request with invalid secret token")
            raise HTTPException(status_code=401, detail="Unauthorized")
    elif get_settings().is_production:
        logger.warning("Webhook secret not configured in production — rejecting request")
        raise HTTPException(status_code=403, detail="Webhook secret not configured")

    body = await request.body()
    if len(body) > MAX_WEBHOOK_BODY_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")

    try:
        data = json.loads(body)
        update = Update.de_json(data, _bot_app.bot)
        await _bot_app.process_update(update)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc
    except Exception:
        logger.exception("Error processing Telegram update")

    return {"ok": True}
