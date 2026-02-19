from datetime import UTC, datetime

from src.models.state import LearningPipelineState
from src.store.knowledge_base import KnowledgeBase


async def update_knowledge_base(
    state: LearningPipelineState,
    *,
    kb: KnowledgeBase,
) -> dict:
    collected = state.get("collected_metrics", [])
    if not collected:
        return {"pattern_updates": []}

    updated_patterns = []

    for metrics in collected:
        pattern_name = metrics.get("pattern_used", "")
        if not pattern_name:
            continue

        perf = await kb.get_pattern_performance(pattern_name)

        old_count = perf.times_used
        perf.times_used += 1
        perf.total_views += metrics.get("views", 0)
        perf.total_likes += metrics.get("likes", 0)
        perf.total_replies += metrics.get("replies", 0)
        perf.total_reposts += metrics.get("reposts", 0)

        total_engagement = perf.total_likes + perf.total_replies + perf.total_reposts
        perf.avg_engagement_rate = (
            total_engagement / perf.total_views if perf.total_views > 0 else 0.0
        )

        follower_delta = metrics.get("follower_delta", 0)
        perf.avg_follower_delta = (
            perf.avg_follower_delta * old_count + follower_delta
        ) / perf.times_used

        engagement_rate = metrics.get("engagement_rate", 0.0)
        threads_id = metrics.get("threads_id", "")
        if perf.best_engagement_rate is None or engagement_rate > perf.best_engagement_rate:
            perf.best_post_id = threads_id
            perf.best_engagement_rate = engagement_rate
        if perf.worst_engagement_rate is None or engagement_rate < perf.worst_engagement_rate:
            perf.worst_post_id = threads_id
            perf.worst_engagement_rate = engagement_rate

        perf.last_used_at = datetime.now(UTC).isoformat()

        await kb.save_pattern_performance(perf)
        updated_patterns.append(perf.model_dump())

    return {"pattern_updates": updated_patterns}
