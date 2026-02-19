"""API route dependencies."""

import hmac
import logging

from fastapi import Header, HTTPException

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    """Verify the API key from the X-Api-Key header.

    If API_SECRET_KEY is not configured, all requests are rejected
    on production and allowed on development.
    """
    settings = get_settings()

    if not settings.api_secret_key:
        if settings.is_production:
            raise HTTPException(status_code=503, detail="API key not configured")
        return

    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_secret_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
