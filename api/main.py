"""FastAPI application - webhook + status endpoints."""

import logging

from fastapi import FastAPI

from api.routes.config import router as config_router
from api.routes.status import router as status_router
from bot.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Threads Agent API",
    description="API for the autonomous Threads growth agent",
    version="0.1.0",
)

app.include_router(webhook_router, tags=["telegram"])
app.include_router(status_router, prefix="/api", tags=["status"])
app.include_router(config_router, prefix="/api", tags=["config"])


@app.get("/health")
async def health():
    return {"status": "ok"}
