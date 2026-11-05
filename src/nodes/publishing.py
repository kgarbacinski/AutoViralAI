import logging
from datetime import UTC, datetime, timedelta

import httpx

from src.messages import (
    PUBLISH_CONTENT_TOO_LONG,
    PUBLISH_EMPTY_CONTENT,
    PUBLISH_FAILED,
    PUBLISH_NO_POST,
    SCHEDULE_NO_PUBLISHED_POST,
)
from src.models.publishing import PublishedPost
from src.models.state import CreationPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.linkedin_api import LINKEDIN_MAX_LENGTH, LinkedInClient

logger = logging.getLogger(__name__)


async def publish_post(
    state: CreationPipelineState,
    *,
    linkedin_client: LinkedInClient,
    kb: KnowledgeBase,
) -> dict:
    selected = state.get("selected_post")
    if not selected:
        return {
            "published_post": None,
            "errors": [PUBLISH_NO_POST],
        }

    content = selected.get("content", "")
    if not content:
        return {
            "published_post": None,
            "errors": [PUBLISH_EMPTY_CONTENT],
        }
    if len(content) > LINKEDIN_MAX_LENGTH:
        return {
            "published_post": None,
            "errors": [
                PUBLISH_CONTENT_TOO_LONG.format(
                    max_length=LINKEDIN_MAX_LENGTH, actual_length=len(content)
                )
            ],
        }

    try:
        post_id = await linkedin_client.publish_post(content)
    except (httpx.HTTPStatusError, httpx.RequestError, TimeoutError, RuntimeError) as e:
        return {
            "published_post": None,
            "errors": [PUBLISH_FAILED.format(error=e)],
        }

    follower_count = state.get("current_follower_count", 0)
    try:
        follower_count = await linkedin_client.get_follower_count()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.warning(
            "Failed to fetch follower count at publish time, using state value: %s",
            e,
        )

    now = datetime.now(UTC)
    published = PublishedPost(
        threads_id=post_id,
        linkedin_id=post_id,
        content=content,
        pattern_used=selected.get("pattern_used", ""),
        pillar=selected.get("pillar", ""),
        published_at=now.isoformat(),
        scheduled_metrics_check=(now + timedelta(hours=48)).isoformat(),
        follower_count_at_publish=follower_count,
        ai_score=selected.get("ai_score", 0.0),
        composite_score=selected.get("composite_score", 0.0),
    )

    await kb.save_published_post(published)

    return {"published_post": published.model_dump()}


async def schedule_metrics_check(
    state: CreationPipelineState,
    *,
    kb: KnowledgeBase,
) -> dict:
    published = state.get("published_post")
    if not published:
        return {"errors": [SCHEDULE_NO_PUBLISHED_POST]}

    post = PublishedPost.model_validate(published)
    await kb.add_pending_metrics(post)
    return {}
