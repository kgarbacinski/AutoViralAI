"""Knowledge base operations wrapping LangGraph Store."""

import json
from datetime import datetime, timezone

from langgraph.store.base import BaseStore

from src.models.publishing import PostMetrics, PublishedPost
from src.models.strategy import AccountNiche, ContentStrategy, PatternPerformance
from src.store.namespaces import (
    ns_config,
    ns_metrics_history,
    ns_pattern_performance,
    ns_pending_metrics,
    ns_published_posts,
    ns_strategy,
)


class KnowledgeBase:
    """Wrapper around LangGraph Store for typed read/write operations."""

    def __init__(self, store: BaseStore, account_id: str):
        self.store = store
        self.account_id = account_id

    async def get_niche_config(self) -> AccountNiche | None:
        items = await self.store.asearch(ns_config(self.account_id))
        if items:
            return AccountNiche.model_validate(items[0].value)
        return None

    async def save_niche_config(self, config: AccountNiche) -> None:
        await self.store.aput(
            ns_config(self.account_id),
            "niche",
            config.model_dump(),
        )

    async def get_strategy(self) -> ContentStrategy:
        items = await self.store.asearch(ns_strategy(self.account_id))
        if items:
            return ContentStrategy.model_validate(items[0].value)
        return ContentStrategy()

    async def save_strategy(self, strategy: ContentStrategy) -> None:
        strategy.last_updated = datetime.now(timezone.utc).isoformat()
        await self.store.aput(
            ns_strategy(self.account_id),
            "current",
            strategy.model_dump(),
        )

    async def get_pattern_performance(self, pattern_name: str) -> PatternPerformance:
        items = await self.store.asearch(ns_pattern_performance(self.account_id))
        for item in items:
            if item.value.get("pattern_name") == pattern_name:
                return PatternPerformance.model_validate(item.value)
        return PatternPerformance(pattern_name=pattern_name)

    async def get_all_pattern_performances(self) -> list[PatternPerformance]:
        items = await self.store.asearch(ns_pattern_performance(self.account_id), limit=100)
        return [PatternPerformance.model_validate(item.value) for item in items]

    async def save_pattern_performance(self, perf: PatternPerformance) -> None:
        await self.store.aput(
            ns_pattern_performance(self.account_id),
            perf.pattern_name,
            perf.model_dump(),
        )

    async def get_recent_posts(self, limit: int = 20) -> list[PublishedPost]:
        items = await self.store.asearch(ns_published_posts(self.account_id), limit=limit)
        return [PublishedPost.model_validate(item.value) for item in items]

    async def save_published_post(self, post: PublishedPost) -> None:
        await self.store.aput(
            ns_published_posts(self.account_id),
            post.threads_id,
            post.model_dump(),
        )

    async def get_pending_metrics_posts(self) -> list[PublishedPost]:
        items = await self.store.asearch(ns_pending_metrics(self.account_id), limit=50)
        return [PublishedPost.model_validate(item.value) for item in items]

    async def add_pending_metrics(self, post: PublishedPost) -> None:
        await self.store.aput(
            ns_pending_metrics(self.account_id),
            post.threads_id,
            post.model_dump(),
        )

    async def remove_pending_metrics(self, threads_id: str) -> None:
        await self.store.adelete(ns_pending_metrics(self.account_id), threads_id)

    async def save_post_metrics(self, metrics: PostMetrics) -> None:
        key = f"{metrics.threads_id}_{metrics.collected_at}"
        await self.store.aput(
            ns_metrics_history(self.account_id),
            key,
            metrics.model_dump(),
        )

    async def get_metrics_history(self, limit: int = 50) -> list[PostMetrics]:
        items = await self.store.asearch(ns_metrics_history(self.account_id), limit=limit)
        return [PostMetrics.model_validate(item.value) for item in items]

    async def get_recent_post_contents(self, limit: int = 20) -> list[str]:
        """Get content strings of recent posts for novelty scoring."""
        posts = await self.get_recent_posts(limit=limit)
        return [p.content for p in posts]
