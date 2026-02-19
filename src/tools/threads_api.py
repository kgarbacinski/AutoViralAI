"""Threads API wrapper with mock implementation for development."""

from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)


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

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


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
        self._client = httpx.AsyncClient(timeout=self.TIMEOUT)

    async def get_follower_count(self) -> int:
        resp = await self._client.get(
            f"{self.base_url}/{self.user_id}/threads_insights",
            params={
                "metric": "followers_count",
                "access_token": self.access_token,
            },
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            return data[0].get("total_value", {}).get("value", 0)
        return 0

    async def publish_post(self, content: str) -> str:
        create_resp = await self._client.post(
            f"{self.base_url}/{self.user_id}/threads",
            params={
                "media_type": "TEXT",
                "text": content,
                "access_token": self.access_token,
            },
        )
        create_resp.raise_for_status()
        container_id = create_resp.json()["id"]

        await self._wait_for_container(container_id)

        publish_resp = await self._client.post(
            f"{self.base_url}/{self.user_id}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": self.access_token,
            },
        )
        publish_resp.raise_for_status()
        return publish_resp.json()["id"]

    async def _wait_for_container(
        self, container_id: str, *, max_attempts: int = 10, interval: float = 2.0
    ) -> None:
        """Poll container status until FINISHED or timeout."""
        for attempt in range(1, max_attempts + 1):
            resp = await self._client.get(
                f"{self.base_url}/{container_id}",
                params={
                    "fields": "status",
                    "access_token": self.access_token,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            logger.info(f"Container {container_id} status: {status} (attempt {attempt})")

            if status == "FINISHED":
                return
            if status == "ERROR":
                error_msg = data.get("error_message", "unknown error")
                raise RuntimeError(f"Threads container {container_id} failed: {error_msg}")

            await asyncio.sleep(interval)

        raise TimeoutError(
            f"Threads container {container_id} did not finish after {max_attempts} attempts"
        )

    async def get_post_metrics(self, threads_id: str) -> dict:
        resp = await self._client.get(
            f"{self.base_url}/{threads_id}/insights",
            params={
                "metric": "views,likes,replies,reposts,quotes",
                "access_token": self.access_token,
            },
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        metrics = {}
        for item in data:
            name = item.get("name")
            values = item.get("values", [])
            if name and values:
                metrics[name] = values[0].get("value", 0)

        views = metrics.get("views", 0)
        total = sum(metrics.get(k, 0) for k in ["likes", "replies", "reposts", "quotes"])
        metrics["engagement_rate"] = total / views if views > 0 else 0
        metrics["threads_id"] = threads_id
        return metrics

    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        resp = await self._client.get(
            f"{self.base_url}/{self.user_id}/threads",
            params={
                "fields": "id,text,timestamp",
                "limit": limit,
                "access_token": self.access_token,
            },
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    async def close(self) -> None:
        await self._client.aclose()


def get_threads_client(settings: Settings) -> ThreadsClient:
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
