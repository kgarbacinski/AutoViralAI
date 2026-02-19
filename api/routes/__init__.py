import hmac
import logging

from fastapi import Header, HTTPException

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()

    if not settings.api_secret_key:
        if settings.is_production:
            raise HTTPException(status_code=503, detail="API key not configured")
        logger.warning("API key auth disabled (development mode, no API_SECRET_KEY set)")
        return

    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_secret_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
