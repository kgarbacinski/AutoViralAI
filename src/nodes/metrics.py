"""Metrics collection node - gathers engagement data for published posts."""

import logging
from datetime import UTC, datetime

from src.models.publishing import PostMetrics
from src.models.state import LearningPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import ThreadsClient

logger = logging.getLogger(__name__)


async def collect_metrics(
    state: LearningPipelineState,
    *,
    threads_client: ThreadsClient,
    kb: KnowledgeBase,
) -> dict:
    """Collect metrics for posts that are due for checking."""
    pending = await kb.get_pending_metrics_posts()
    now = datetime.now(UTC)

    collected = []
    errors = []

    # Fetch follower count once for all posts in this cycle
    current_followers = None
    try:
        current_followers = await threads_client.get_follower_count()
    except Exception:
        logger.warning("Failed to fetch follower count for metrics cycle", exc_info=True)

    for post in pending:
        if post.scheduled_metrics_check:
            check_time = datetime.fromisoformat(post.scheduled_metrics_check)
            if check_time.tzinfo is None:
                check_time = check_time.replace(tzinfo=UTC)
            if now < check_time:
                continue

        try:
            raw_metrics = await threads_client.get_post_metrics(post.threads_id)
        except Exception as e:
            errors.append(f"collect_metrics: Failed for {post.threads_id}: {e}")
            continue

        publish_time = datetime.fromisoformat(post.published_at)
        if publish_time.tzinfo is None:
            publish_time = publish_time.replace(tzinfo=UTC)
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

        if current_followers is not None:
            metrics.follower_delta = current_followers - post.follower_count_at_publish

        collected.append(metrics)

        await kb.save_post_metrics(metrics)
        await kb.remove_pending_metrics(post.threads_id)

    return {
        "posts_to_check": [p.model_dump() for p in pending],
        "collected_metrics": [m.model_dump() for m in collected],
        "errors": errors,
    }
