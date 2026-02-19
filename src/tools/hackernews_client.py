"""Hacker News API client for viral tech content research.

Uses the free Firebase-based HN API — no auth required.
https://github.com/HackerNews/API
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import httpx

from src.models.research import ViralPost

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
MIN_HN_SCORE = 50


class HackerNewsClient(ABC):
    """Abstract HackerNews client for viral content research."""

    @abstractmethod
    async def get_viral_posts(self, limit: int = 30) -> list[ViralPost]: ...

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class MockHackerNewsClient(HackerNewsClient):
    """Mock client for development — returns sample HN posts."""

    async def get_viral_posts(self, limit: int = 30) -> list[ViralPost]:
        return [
            ViralPost(
                platform="hackernews",
                author="pg",
                content="Show HN: A new way to build web apps with AI",
                url="https://news.ycombinator.com/item?id=1",
                likes=350,
                replies=120,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["webdev", "ai"],
            ),
            ViralPost(
                platform="hackernews",
                author="dang",
                content="Why Rust is taking over systems programming",
                url="https://news.ycombinator.com/item?id=2",
                likes=275,
                replies=89,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["rust", "systems"],
            ),
        ]


class RealHackerNewsClient(HackerNewsClient):
    """Real HN client — fetches top/best stories via Firebase API."""

    def __init__(self, timeout: float = 20.0):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get_viral_posts(self, limit: int = 30) -> list[ViralPost]:
        """Get top HN stories as viral post research material."""
        # Fetch top + best story IDs concurrently
        top_resp, best_resp = await asyncio.gather(
            self._client.get(f"{HN_BASE_URL}/topstories.json"),
            self._client.get(f"{HN_BASE_URL}/beststories.json"),
        )
        top_ids = []
        best_ids = []
        try:
            top_resp.raise_for_status()
            top_ids = top_resp.json()[:limit]
        except httpx.HTTPStatusError:
            logger.warning("Failed to fetch HN top stories")
        try:
            best_resp.raise_for_status()
            best_ids = best_resp.json()[:limit]
        except httpx.HTTPStatusError:
            logger.warning("Failed to fetch HN best stories")

        # Deduplicate, keep order
        seen = set()
        all_ids = []
        for sid in top_ids + best_ids:
            if sid not in seen:
                seen.add(sid)
                all_ids.append(sid)

        # Fetch story details concurrently
        tasks = [self._fetch_story(sid) for sid in all_ids[:limit]]
        stories = await asyncio.gather(*tasks, return_exceptions=True)

        posts = []
        failure_count = 0
        for story in stories:
            if isinstance(story, Exception):
                failure_count += 1
                continue
            if story and story.get("score", 0) >= MIN_HN_SCORE:
                posts.append(
                    ViralPost(
                        platform="hackernews",
                        author=story.get("by", "unknown"),
                        content=story.get("title", ""),
                        url=story.get(
                            "url", f"https://news.ycombinator.com/item?id={story.get('id', '')}"
                        ),
                        likes=story.get("score", 0),
                        replies=story.get("descendants", 0),
                        reposts=0,
                        views=0,
                        engagement_rate=0.0,
                        topic_tags=[],
                    )
                )

        if failure_count:
            logger.warning("HackerNews: %d/%d story fetches failed", failure_count, len(stories))
        logger.info("HackerNews: fetched %d viral stories", len(posts))
        return posts

    async def _fetch_story(self, story_id: int) -> dict | None:
        resp = await self._client.get(f"{HN_BASE_URL}/item/{story_id}.json")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if (
            data
            and data.get("type") == "story"
            and not data.get("dead")
            and not data.get("deleted")
        ):
            return data
        return None

    async def close(self) -> None:
        await self._client.aclose()


def get_hackernews_client(settings: Settings) -> HackerNewsClient:
    """Factory: returns real client in production, mock in development."""
    if settings.is_production:
        return RealHackerNewsClient()
    return MockHackerNewsClient()
