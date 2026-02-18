"""Status and health endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get agent status overview."""
    return {
        "status": "running",
        "pipelines": {
            "creation": "idle",
            "learning": "idle",
        },
        "stats": {
            "total_posts": 0,
            "current_followers": 0,
            "target_followers": 100,
        },
    }
