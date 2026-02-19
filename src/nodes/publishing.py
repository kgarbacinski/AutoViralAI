"""Publishing node - publishes approved posts to Threads."""

from datetime import datetime, timedelta, timezone

from src.models.publishing import PublishedPost
from src.models.state import CreationPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import ThreadsClient


async def publish_post(
    state: CreationPipelineState,
    *,
    threads_client: ThreadsClient,
    kb: KnowledgeBase,
) -> dict:
    """Publish the approved post to Threads and save to knowledge base."""
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

    try:
        threads_id = await threads_client.publish_post(content)
    except Exception as e:
        return {
            "published_post": None,
            "errors": [f"publish_post: Failed to publish: {e}"],
        }

    follower_count = 0
    try:
        follower_count = await threads_client.get_follower_count()
    except Exception:
        pass

    now = datetime.now(timezone.utc)
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
    """Register the published post for future metrics collection."""
    published = state.get("published_post")
    if not published:
        return {}

    post = PublishedPost.model_validate(published)
    await kb.add_pending_metrics(post)
    return {}
