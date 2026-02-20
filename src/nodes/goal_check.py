import httpx

from src.models.state import CreationPipelineState
from src.tools.threads_api import ThreadsClient


async def goal_check(
    state: CreationPipelineState,
    *,
    threads_client: ThreadsClient,
) -> dict:
    try:
        current = await threads_client.get_follower_count()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return {
            "current_follower_count": state.get("current_follower_count", 0),
            "goal_reached": False,
            "errors": [f"goal_check: Failed to get follower count: {e}"],
        }

    target = state.get("target_follower_count", 100)
    return {
        "current_follower_count": current,
        "target_follower_count": target,
        "goal_reached": current >= target,
    }
