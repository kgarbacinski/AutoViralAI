import logging
from datetime import UTC, datetime

from langgraph.store.base import BaseStore

from src.exceptions import KnowledgeBaseError
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

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self, store: BaseStore, account_id: str):
        self.store = store
        self.account_id = account_id

    async def get_niche_config(self) -> AccountNiche | None:
        try:
            item = await self.store.aget(ns_config(self.account_id), "niche")
            if item:
                return AccountNiche.model_validate(item.value)
            return None
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get niche config: {e}") from e

    async def save_niche_config(self, config: AccountNiche) -> None:
        try:
            await self.store.aput(
                ns_config(self.account_id),
                "niche",
                config.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save niche config: {e}") from e

    async def get_strategy(self) -> ContentStrategy:
        try:
            item = await self.store.aget(ns_strategy(self.account_id), "current")
            if item:
                return ContentStrategy.model_validate(item.value)
            return ContentStrategy()
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get strategy: {e}") from e

    async def save_strategy(self, strategy: ContentStrategy) -> None:
        updated = strategy.model_copy(update={"last_updated": datetime.now(UTC).isoformat()})
        try:
            await self.store.aput(
                ns_strategy(self.account_id),
                "current",
                updated.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save strategy: {e}") from e

    async def get_pattern_performance(self, pattern_name: str) -> PatternPerformance:
        try:
            item = await self.store.aget(ns_pattern_performance(self.account_id), pattern_name)
            if item:
                return PatternPerformance.model_validate(item.value)
            return PatternPerformance(pattern_name=pattern_name)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get pattern performance: {e}") from e

    async def get_all_pattern_performances(self) -> list[PatternPerformance]:
        try:
            items = await self.store.asearch(ns_pattern_performance(self.account_id), limit=500)
            return [PatternPerformance.model_validate(item.value) for item in items]
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get all pattern performances: {e}") from e

    async def save_pattern_performance(self, perf: PatternPerformance) -> None:
        try:
            await self.store.aput(
                ns_pattern_performance(self.account_id),
                perf.pattern_name,
                perf.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save pattern performance: {e}") from e

    async def get_recent_posts(self, limit: int = 20) -> list[PublishedPost]:
        try:
            items = await self.store.asearch(ns_published_posts(self.account_id), limit=limit)
            return [PublishedPost.model_validate(item.value) for item in items]
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get recent posts: {e}") from e

    async def save_published_post(self, post: PublishedPost) -> None:
        try:
            await self.store.aput(
                ns_published_posts(self.account_id),
                post.threads_id,
                post.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save published post: {e}") from e

    async def get_pending_metrics_posts(self) -> list[PublishedPost]:
        try:
            items = await self.store.asearch(ns_pending_metrics(self.account_id), limit=50)
            return [PublishedPost.model_validate(item.value) for item in items]
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get pending metrics posts: {e}") from e

    async def add_pending_metrics(self, post: PublishedPost) -> None:
        try:
            await self.store.aput(
                ns_pending_metrics(self.account_id),
                post.threads_id,
                post.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to add pending metrics: {e}") from e

    async def remove_pending_metrics(self, threads_id: str) -> None:
        try:
            await self.store.adelete(ns_pending_metrics(self.account_id), threads_id)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to remove pending metrics: {e}") from e

    async def save_post_metrics(self, metrics: PostMetrics) -> None:
        key = f"{metrics.threads_id}_{metrics.collected_at}"
        try:
            await self.store.aput(
                ns_metrics_history(self.account_id),
                key,
                metrics.model_dump(),
            )
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save post metrics: {e}") from e

    async def get_metrics_history(self, limit: int = 50) -> list[PostMetrics]:
        try:
            items = await self.store.asearch(ns_metrics_history(self.account_id), limit=limit)
            return [PostMetrics.model_validate(item.value) for item in items]
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to get metrics history: {e}") from e

    async def get_recent_post_contents(self, limit: int = 20) -> list[str]:
        posts = await self.get_recent_posts(limit=limit)
        return [p.content for p in posts]

    async def cleanup_old_metrics(self, keep_last: int = 200) -> int:
        try:
            items = await self.store.asearch(ns_metrics_history(self.account_id), limit=1000)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to search metrics for cleanup: {e}") from e
        if len(items) <= keep_last:
            return 0
        sorted_items = sorted(items, key=lambda i: i.value.get("collected_at", ""))
        to_delete = sorted_items[:-keep_last]
        deleted = 0
        for item in to_delete:
            try:
                await self.store.adelete(ns_metrics_history(self.account_id), item.key)
                deleted += 1
            except Exception as e:
                logger.warning("Failed to delete old metric %s: %s", item.key, e)
        return deleted
