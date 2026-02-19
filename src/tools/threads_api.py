from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


class ThreadsClient(ABC):
    @abstractmethod
    async def get_follower_count(self) -> int: ...

    @abstractmethod
    async def publish_post(self, content: str) -> str: ...

    @abstractmethod
    async def get_post_metrics(self, threads_id: str) -> dict: ...

    @abstractmethod
    async def get_user_posts(self, limit: int = 25) -> list[dict]: ...

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class MockThreadsClient(ThreadsClient):
    def __init__(self, initial_followers: int = 12):
        self._follower_count = initial_followers
        self._posts: dict[str, dict] = {}
        self._post_counter = 0

    async def get_follower_count(self) -> int:
        self._follower_count += random.randint(0, 3)
        return self._follower_count

    async def publish_post(self, content: str) -> str:
        self._post_counter += 1
        threads_id = f"mock_{self._post_counter}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        self._posts[threads_id] = {
            "id": threads_id,
            "content": content,
            "published_at": datetime.now(UTC).isoformat(),
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
    TIMEOUT = httpx.Timeout(10.0, connect=5.0)

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://graph.threads.net/v1.0"
        self._client = httpx.AsyncClient(timeout=self.TIMEOUT)

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(_MAX_RETRIES):
            resp = await self._client.request(method, url, **kwargs)
            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "Threads API %d on %s, retrying in %.1fs (attempt %d/%d)",
                    resp.status_code,
                    url.split("?")[0],
                    delay,
                    attempt + 1,
                    _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
                continue
            resp.raise_for_status()
            return resp
        return resp

    async def get_follower_count(self) -> int:
        resp = await self._request_with_retry(
            "GET",
            f"{self.base_url}/{self.user_id}/threads_insights",
            params={
                "metric": "followers_count",
                "access_token": self.access_token,
            },
        )
        data = resp.json().get("data", [])
        if data:
            return data[0].get("total_value", {}).get("value", 0)
        return 0

    async def publish_post(self, content: str) -> str:
        create_resp = await self._request_with_retry(
            "POST",
            f"{self.base_url}/{self.user_id}/threads",
            params={
                "media_type": "TEXT",
                "text": content,
                "access_token": self.access_token,
            },
        )
        container_id = create_resp.json()["id"]

        try:
            await self._wait_for_container(container_id)
        except (TimeoutError, RuntimeError):
            logger.error("Container %s failed; cannot publish", container_id)
            raise

        publish_resp = await self._request_with_retry(
            "POST",
            f"{self.base_url}/{self.user_id}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": self.access_token,
            },
        )
        return publish_resp.json()["id"]

    async def _wait_for_container(
        self, container_id: str, *, max_attempts: int = 10, initial_interval: float = 1.0
    ) -> None:
        interval = initial_interval
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
            logger.info("Container %s status: %s (attempt %d)", container_id, status, attempt)

            if status == "FINISHED":
                return
            if status == "ERROR":
                error_msg = data.get("error_message", "unknown error")
                raise RuntimeError(f"Threads container {container_id} failed: {error_msg}")

            await asyncio.sleep(interval)
            interval = min(interval * 1.5, 10.0)

        raise TimeoutError(
            f"Threads container {container_id} did not finish after {max_attempts} attempts"
        )

    async def get_post_metrics(self, threads_id: str) -> dict:
        resp = await self._request_with_retry(
            "GET",
            f"{self.base_url}/{threads_id}/insights",
            params={
                "metric": "views,likes,replies,reposts,quotes",
                "access_token": self.access_token,
            },
        )
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
        resp = await self._request_with_retry(
            "GET",
            f"{self.base_url}/{self.user_id}/threads",
            params={
                "fields": "id,text,timestamp",
                "limit": limit,
                "access_token": self.access_token,
            },
        )
        return resp.json().get("data", [])

    async def close(self) -> None:
        await self._client.aclose()


def get_threads_client(settings: Settings) -> ThreadsClient:
    if settings.is_production:
        if not settings.threads_access_token:
            raise ValueError(
                "THREADS_ACCESS_TOKEN is required in production. "
                "Get it from https://developers.facebook.com (Threads API)."
            )
        if not settings.threads_user_id:
            raise ValueError("THREADS_USER_ID is required in production.")
        return RealThreadsClient(
            access_token=settings.threads_access_token,
            user_id=settings.threads_user_id,
        )
    return MockThreadsClient()
