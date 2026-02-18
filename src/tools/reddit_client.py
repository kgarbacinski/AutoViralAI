"""Reddit API wrapper using PRAW for viral content research."""

import asyncio
from abc import ABC, abstractmethod

import praw

from src.models.research import ViralPost


class RedditResearcher(ABC):
    @abstractmethod
    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]: ...


class MockRedditResearcher(RedditResearcher):
    """Mock for development - returns sample viral posts."""

    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]:
        return [
            ViralPost(
                platform="reddit",
                author="u/techdev42",
                content="Hot take: Most developers don't need microservices. A well-structured monolith handles 99% of use cases better. Stop overengineering.",
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
                content="I replaced 80% of my Google searches with Claude. Not because AI is always right, but because it gives me a starting point that's 10x faster to verify than to search from scratch.",
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
                content="After 3 failed startups, here's what I wish I knew: Your first 100 users matter more than your first 100,000 lines of code. Ship ugly, ship fast, ship often.",
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
                content="The best debugging technique nobody talks about: explain your code to a rubber duck. Sounds stupid. Works every time. Something about verbalizing forces your brain to process differently.",
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
                content="Unpopular opinion: Leetcode grinding is a waste of time for 90% of developers. The companies that require it are not the only good companies to work for.",
                url="https://reddit.com/r/cscareerquestions/mock5",
                likes=6789,
                replies=1023,
                reposts=0,
                views=0,
                engagement_rate=0.0,
                topic_tags=["career", "hot_take"],
            ),
        ]


class RealRedditResearcher(RedditResearcher):
    """Real Reddit client using PRAW."""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    async def search_viral_posts(
        self, subreddits: list[str], query: str, limit: int = 20
    ) -> list[ViralPost]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._search_sync, subreddits, query, limit
        )

    def _search_sync(
        self, subreddits: list[str], query: str, limit: int
    ) -> list[ViralPost]:
        posts = []
        for sub_name in subreddits:
            subreddit = self.reddit.subreddit(sub_name)
            for submission in subreddit.search(query, sort="top", time_filter="week", limit=limit):
                if submission.score < 100:
                    continue
                posts.append(
                    ViralPost(
                        platform="reddit",
                        author=f"u/{submission.author.name}" if submission.author else "deleted",
                        content=submission.selftext[:500] if submission.is_self else submission.title,
                        url=f"https://reddit.com{submission.permalink}",
                        likes=submission.score,
                        replies=submission.num_comments,
                        topic_tags=[],
                    )
                )
        return posts


def get_reddit_researcher(settings) -> RedditResearcher:
    if settings.reddit_client_id and settings.env == "production":
        return RealRedditResearcher(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    return MockRedditResearcher()
