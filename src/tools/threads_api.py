"""Threads API wrapper with mock implementation for development."""

import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx


class ThreadsClient(ABC):
    """Abstract Threads API client."""

    @abstractmethod
    async def get_follower_count(self) -> int: ...

    @abstractmethod
    async def publish_post(self, content: str) -> str:
        """Publish a post. Returns the media container ID."""
        ...

    @abstractmethod
    async def get_post_metrics(self, threads_id: str) -> dict:
        """Get engagement metrics for a post."""
        ...

    @abstractmethod
    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        """Get recent posts from the authenticated user."""
        ...


class MockThreadsClient(ThreadsClient):
    """Mock client for development - returns fake but realistic data."""

    def __init__(self, initial_followers: int = 12):
        self._follower_count = initial_followers
        self._posts: dict[str, dict] = {}
        self._post_counter = 0

    async def get_follower_count(self) -> int:
        self._follower_count += random.randint(0, 3)
        return self._follower_count

    async def publish_post(self, content: str) -> str:
        self._post_counter += 1
        threads_id = (
            f"mock_{self._post_counter}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )
        self._posts[threads_id] = {
            "id": threads_id,
            "content": content,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        return threads_id

    async def get_post_metrics(self, threads_id: str) -> dict:
        views = random.randint(50, 5000)
        likes = int(views * random.uniform(0.02, 0.15))
        replies = int(views * random.uniform(0.005, 0.03))
        reposts = int(views * random.uniform(0.002, 0.02))
        quotes = int(views * random.uniform(0.001, 0.01))
        total_engagement = likes + replies + reposts + quotes
        return {
            "threads_id": threads_id,
            "views": views,
            "likes": likes,
            "replies": replies,
            "reposts": reposts,
            "quotes": quotes,
            "engagement_rate": total_engagement / views if views > 0 else 0,
        }

    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        posts = list(self._posts.values())
        return posts[-limit:]


class RealThreadsClient(ThreadsClient):
    """Real Threads API client - to be implemented when API access is granted."""

    TIMEOUT = httpx.Timeout(10.0, connect=5.0)

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://graph.threads.net/v1.0"

    async def get_follower_count(self) -> int:
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/{self.user_id}",
                params={
                    "fields": "followers_count",
                    "access_token": self.access_token,
                },
            )
            resp.raise_for_status()
            return resp.json()["followers_count"]

    async def publish_post(self, content: str) -> str:
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            create_resp = await client.post(
                f"{self.base_url}/{self.user_id}/threads",
                params={
                    "media_type": "TEXT",
                    "text": content,
                    "access_token": self.access_token,
                },
            )
            create_resp.raise_for_status()
            container_id = create_resp.json()["id"]

            publish_resp = await client.post(
                f"{self.base_url}/{self.user_id}/threads_publish",
                params={
                    "creation_id": container_id,
                    "access_token": self.access_token,
                },
            )
            publish_resp.raise_for_status()
            return publish_resp.json()["id"]

    async def get_post_metrics(self, threads_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/{threads_id}/insights",
                params={
                    "metric": "views,likes,replies,reposts,quotes",
                    "access_token": self.access_token,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            metrics = {item["name"]: item["values"][0]["value"] for item in data}
            views = metrics.get("views", 0)
            total = sum(metrics.get(k, 0) for k in ["likes", "replies", "reposts", "quotes"])
            metrics["engagement_rate"] = total / views if views > 0 else 0
            metrics["threads_id"] = threads_id
            return metrics

    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/{self.user_id}/threads",
                params={
                    "fields": "id,text,timestamp",
                    "limit": limit,
                    "access_token": self.access_token,
                },
            )
            resp.raise_for_status()
            return resp.json().get("data", [])


def get_threads_client(settings) -> ThreadsClient:
    """Factory: returns real client in production, mock in development."""
    if settings.is_production:
        if not settings.threads_access_token:
            raise ValueError(
                "THREADS_ACCESS_TOKEN is required in production. "
                "Get it from https://developers.facebook.com (Threads API)."
            )
        return RealThreadsClient(
            access_token=settings.threads_access_token,
            user_id=settings.threads_user_id,
        )
    return MockThreadsClient()
