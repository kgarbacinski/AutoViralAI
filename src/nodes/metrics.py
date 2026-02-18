"""Metrics collection node - gathers engagement data for published posts."""

from datetime import datetime, timezone

from src.models.publishing import PostMetrics
from src.models.state import LearningPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import ThreadsClient


async def collect_metrics(
    state: LearningPipelineState,
    *,
    threads_client: ThreadsClient,
    kb: KnowledgeBase,
) -> dict:
    """Collect metrics for posts that are due for checking."""
    pending = await kb.get_pending_metrics_posts()
    now = datetime.now(timezone.utc)

    collected = []
    errors = []

    for post in pending:
        if post.scheduled_metrics_check:
            check_time = datetime.fromisoformat(post.scheduled_metrics_check)
            if now < check_time:
                continue

        try:
            raw_metrics = await threads_client.get_post_metrics(post.threads_id)
        except Exception as e:
            errors.append(f"collect_metrics: Failed for {post.threads_id}: {e}")
            continue

        publish_time = datetime.fromisoformat(post.published_at)
        hours_elapsed = (now - publish_time).total_seconds() / 3600

        metrics = PostMetrics(
            threads_id=post.threads_id,
            content=post.content,
            pattern_used=post.pattern_used,
            pillar=post.pillar,
            views=raw_metrics.get("views", 0),
            likes=raw_metrics.get("likes", 0),
            replies=raw_metrics.get("replies", 0),
            reposts=raw_metrics.get("reposts", 0),
            quotes=raw_metrics.get("quotes", 0),
            engagement_rate=raw_metrics.get("engagement_rate", 0.0),
            collected_at=now.isoformat(),
            hours_since_publish=hours_elapsed,
        )

        try:
            followers = await threads_client.get_follower_count()
            metrics.follower_delta = followers - (followers or 0)
        except Exception:
            pass

        collected.append(metrics)

        await kb.save_post_metrics(metrics)
        await kb.remove_pending_metrics(post.threads_id)

    return {
        "posts_to_check": [p.model_dump() for p in pending],
        "collected_metrics": [m.model_dump() for m in collected],
        "errors": errors if errors else [],
    }
