"""Status and health endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """Get agent status overview with live orchestrator data."""
    orchestrator = getattr(request.app.state, "orchestrator", None)

    if orchestrator is None:
        return {
            "status": "starting",
            "pipelines": {"creation": "unknown", "learning": "unknown"},
            "stats": {},
        }

    pending = orchestrator.pending_approvals
    jobs = orchestrator.get_scheduled_jobs()

    return {
        "status": "running",
        "pipelines": {
            "creation": {
                "cycles_completed": orchestrator._creation_cycle,
                "pending_approvals": len(pending),
                "pending_thread_ids": list(pending.keys()),
            },
            "learning": {
                "cycles_completed": orchestrator._learning_cycle,
            },
        },
        "scheduled_jobs": jobs,
        "stats": {
            "target_followers": orchestrator.settings.target_followers,
        },
    }
