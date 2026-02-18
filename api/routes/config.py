"""Configuration endpoints."""

from pathlib import Path

import yaml
from fastapi import APIRouter

from config.settings import get_settings

router = APIRouter()


@router.get("/config/niche")
async def get_niche_config():
    """Get current niche configuration."""
    settings = get_settings()
    config_path = settings.niche_config_path
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {"error": "Niche config not found"}
