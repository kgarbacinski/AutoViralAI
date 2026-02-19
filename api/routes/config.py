import asyncio

import yaml
from fastapi import APIRouter, Depends, HTTPException

from api.messages import NICHE_CONFIG_NOT_FOUND
from api.routes import verify_api_key
from config.settings import get_settings

router = APIRouter()


@router.get("/config/niche")
async def get_niche_config(_=Depends(verify_api_key)):
    settings = get_settings()
    config_path = settings.niche_config_path

    if not config_path.exists():
        raise HTTPException(status_code=404, detail=NICHE_CONFIG_NOT_FOUND)

    content = await asyncio.to_thread(config_path.read_text)
    return yaml.safe_load(content)
