"""Reddit API wrapper using asyncpraw for viral content research."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import asyncpraw

from src.models.research import ViralPost

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)


class RedditResearcher(ABC):
    @abstractmethod
    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]: ...

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class MockRedditResearcher(RedditResearcher):
    """Mock for development - returns sample viral posts."""

    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]:
        mock_posts = [
            ViralPost(
                platform="reddit",
                author="u/techdev42",
                content=(
                    "Hot take: Most developers don't need microservices. "
                    "A well-structured monolith handles 99% of use cases better. "
                    "Stop overengineering."
                ),
                url="https://reddit.com/r/programming/mock1",
                likes=2847,
                replies=432,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["architecture", "hot_take"],
            ),
            ViralPost(
                platform="reddit",
                author="u/ai_researcher",
                content=(
                    "I replaced 80% of my Google searches with Claude. "
                    "Not because AI is always right, but because it gives me a starting "
                    "point that's 10x faster to verify than to search from scratch."
                ),
                url="https://reddit.com/r/programming/mock2",
                likes=5123,
                replies=891,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["ai", "productivity"],
            ),
            ViralPost(
                platform="reddit",
                author="u/startup_founder",
                content=(
                    "After 3 failed startups, here's what I wish I knew: "
                    "Your first 100 users matter more than your first 100,000 lines of code. "
                    "Ship ugly, ship fast, ship often."
                ),
                url="https://reddit.com/r/startups/mock3",
                likes=3456,
                replies=267,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["startup", "advice"],
            ),
            ViralPost(
                platform="reddit",
                author="u/senior_dev",
                content=(
                    "The best debugging technique nobody talks about: "
                    "explain your code to a rubber duck. Sounds stupid. Works every time. "
                    "Something about verbalizing forces your brain to process differently."
                ),
                url="https://reddit.com/r/programming/mock4",
                likes=4210,
                replies=356,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["debugging", "practical_tip"],
            ),
            ViralPost(
                platform="reddit",
                author="u/career_dev",
                content=(
                    "Unpopular opinion: Leetcode grinding is a waste of time for "
                    "90% of developers. The companies that require it are not the "
                    "only good companies to work for."
                ),
                url="https://reddit.com/r/cscareerquestions/mock5",
                likes=6789,
                replies=1023,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["career", "hot_take"],
            ),
        ]
        return mock_posts[:limit]


class RealRedditResearcher(RedditResearcher):
    """Real Reddit client using asyncpraw (async-native)."""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self._reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]:
        tasks = [self._search_subreddit(sub, query, limit) for sub in subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        posts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Reddit search failed for r/%s: %s", subreddits[i], result)
                continue
            posts.extend(result)
        return posts

    async def _search_subreddit(self, sub_name: str, query: str, limit: int) -> list[ViralPost]:
        """Search a single subreddit for viral posts."""
        posts = []
        subreddit = await self._reddit.subreddit(sub_name)
        async for submission in subreddit.search(
            query, sort="top", time_filter="week", limit=limit
        ):
            if submission.score < 100:
                continue
            author_name = f"u/{submission.author.name}" if submission.author else "deleted"
            content = submission.selftext[:500] if submission.is_self else submission.title
            posts.append(
                ViralPost(
                    platform="reddit",
                    author=author_name,
                    content=content,
                    url=f"https://reddit.com{submission.permalink}",
                    likes=submission.score,
                    replies=submission.num_comments,
                    topic_tags=[],
                )
            )
        return posts

    async def close(self) -> None:
        await self._reddit.close()


def get_reddit_researcher(settings: Settings) -> RedditResearcher:
    """Factory: returns real client in production, mock in development."""
    if settings.is_production:
        missing = []
        if not settings.reddit_client_id:
            missing.append("REDDIT_CLIENT_ID")
        if not settings.reddit_client_secret:
            missing.append("REDDIT_CLIENT_SECRET")
        if not settings.reddit_user_agent:
            missing.append("REDDIT_USER_AGENT")
        if missing:
            raise ValueError(
                f"{', '.join(missing)} required in production. "
                "Get credentials from https://www.reddit.com/prefs/apps"
            )
        return RealRedditResearcher(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    return MockRedditResearcher()
