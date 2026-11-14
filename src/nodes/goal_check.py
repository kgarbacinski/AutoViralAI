import httpx

from src.models.state import CreationPipelineState
from src.tools.linkedin_api import LinkedInClient


async def goal_check(
    state: CreationPipelineState,
    *,
    linkedin_client: LinkedInClient,
) -> dict:
    try:
        current = await linkedin_client.get_follower_count()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return {
            "current_follower_count": state.get("current_follower_count", 0),
            "goal_reached": False,
            "errors": [f"goal_check: Failed to get follower count: {e}"],
        }

    target = state.get("target_follower_count", 0)
    return {
        "current_follower_count": current,
        "target_follower_count": target,
        "goal_reached": current >= target and target > 0,
    }
