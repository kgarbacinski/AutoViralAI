import logging
from datetime import UTC, datetime, timedelta

from src.models.publishing import PublishedPost
from src.models.state import CreationPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import ThreadsClient

logger = logging.getLogger(__name__)

THREADS_MAX_LENGTH = 500


async def publish_post(
    state: CreationPipelineState,
    *,
    threads_client: ThreadsClient,
    kb: KnowledgeBase,
) -> dict:
    selected = state.get("selected_post")
    if not selected:
        return {
            "published_post": None,
            "errors": ["publish_post: No post to publish"],
        }

    content = selected.get("content", "")
    if not content:
        return {
            "published_post": None,
            "errors": ["publish_post: Post content is empty"],
        }
    if len(content) > THREADS_MAX_LENGTH:
        return {
            "published_post": None,
            "errors": [
                f"publish_post: Content exceeds {THREADS_MAX_LENGTH} chars ({len(content)})"
            ],
        }

    try:
        threads_id = await threads_client.publish_post(content)
    except Exception as e:
        return {
            "published_post": None,
            "errors": [f"publish_post: Failed to publish: {e}"],
        }

    follower_count = state.get("current_follower_count", 0)
    try:
        follower_count = await threads_client.get_follower_count()
    except Exception:
        logger.warning(
            "Failed to fetch follower count at publish time, using state value",
            exc_info=True,
        )

    now = datetime.now(UTC)
    published = PublishedPost(
        threads_id=threads_id,
        content=content,
        pattern_used=selected.get("pattern_used", ""),
        pillar=selected.get("pillar", ""),
        published_at=now.isoformat(),
        scheduled_metrics_check=(now + timedelta(hours=24)).isoformat(),
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
        return {"errors": ["schedule_metrics_check: No published post to schedule"]}

    post = PublishedPost.model_validate(published)
    await kb.add_pending_metrics(post)
    return {}
