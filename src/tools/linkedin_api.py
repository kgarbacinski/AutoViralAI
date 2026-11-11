from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import quote

import httpx

from src.messages import LINKEDIN_ACCESS_TOKEN_REQUIRED, LINKEDIN_AUTHOR_URN_REQUIRED

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0

LINKEDIN_MAX_LENGTH = 3000


class LinkedInClient(ABC):
    @abstractmethod
    async def get_follower_count(self) -> int: ...

    @abstractmethod
    async def publish_post(self, content: str) -> str: ...

    @abstractmethod
    async def get_post_metrics(self, post_id: str) -> dict: ...

    @abstractmethod
    async def get_user_posts(self, limit: int = 25) -> list[dict]: ...

    async def refresh_access_token(self) -> str | None:
        return None

    def set_access_token(self, token: str) -> None:
        pass

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class MockLinkedInClient(LinkedInClient):
    def __init__(self, initial_followers: int = 12):
        self._follower_count = initial_followers
        self._posts: dict[str, dict] = {}
        self._post_counter = 0

    async def get_follower_count(self) -> int:
        self._follower_count += random.randint(0, 5)
        return self._follower_count

    async def publish_post(self, content: str) -> str:
        self._post_counter += 1
        post_id = f"mock_linkedin_{self._post_counter}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        self._posts[post_id] = {
            "id": post_id,
            "content": content,
            "published_at": datetime.now(UTC).isoformat(),
        }
        return post_id

    async def get_post_metrics(self, post_id: str) -> dict:
        views = random.randint(100, 10000)
        likes = int(views * random.uniform(0.02, 0.12))
        comments = int(views * random.uniform(0.005, 0.03))
        reposts = int(views * random.uniform(0.002, 0.02))
        total_engagement = likes + comments + reposts
        return {
            "linkedin_id": post_id,
            "views": views,
            "likes": likes,
            "replies": comments,
            "comments": comments,
            "reposts": reposts,
            "quotes": 0,
            "engagement_rate": total_engagement / views if views > 0 else 0,
        }

    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        posts = list(self._posts.values())
        return posts[-limit:]


class RealLinkedInClient(LinkedInClient):
    TIMEOUT = httpx.Timeout(10.0, connect=5.0)

    def __init__(self, access_token: str, author_urn: str, linkedin_version: str = "202511"):
        self.access_token = access_token
        self.author_urn = author_urn
        self.linkedin_version = linkedin_version
        self.base_url = "https://api.linkedin.com"
        self._client = httpx.AsyncClient(timeout=self.TIMEOUT)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": self.linkedin_version,
            "Content-Type": "application/json",
        }

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(_MAX_RETRIES):
            resp = await self._client.request(method, url, **kwargs)
            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "LinkedIn API %d on %s, retrying in %.1fs (attempt %d/%d)",
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

    async def get_follower_count(self, company_id: str | None = None) -> int:
        """LinkedIn member API has no follower count. For company pages use
        /v2/organizationAcls + network size via recommendations API.

        Returns 0 with a warning when not determinable; goal_check tolerates
        0 (goal reached only when target is 0 as well).
        """
        logger.warning(
            "LinkedIn get_follower_count: no public API for member follower count; "
            "returning 0 (set TARGET_FOLLOWERS=0 or use manual goal). "
            "For orgs: GET /v2/companies/{id}/network-size "
            "with r_organization_social scope."
        )
        return 0

    async def publish_post(self, content: str) -> str:
        if not self.author_urn:
            raise ValueError(LINKEDIN_AUTHOR_URN_REQUIRED)
        body = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }
        resp = await self._request_with_retry(
            "POST",
            f"{self.base_url}/v2/ugcPosts",
            headers=self._headers(),
            json=body,
        )
        post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
        if not post_id:
            data = resp.json() if resp.content else {}
            post_id = data.get("id", "")
        if not post_id:
            raise RuntimeError(
                f"LinkedIn publish succeeded but no post ID returned: {resp.text[:500]}"
            )
        return post_id

    async def get_post_metrics(self, post_id: str) -> dict:
        ugc_urn = post_id if post_id.startswith("urn:li:") else f"urn:li:ugcPost:{post_id}"
        encoded = quote(ugc_urn, safe="")
        try:
            resp = await self._request_with_retry(
                "GET",
                f"{self.base_url}/rest/socialActions/{encoded}",
                headers=self._headers(),
            )
            data = resp.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("LinkedIn socialActions failed for %s: %s", post_id, e)
            data = {}
        likes = 0
        comments = 0
        if isinstance(data, dict):
            likes_summary = data.get("likesSummary") or {}
            comments_summary = data.get("commentsSummary") or {}
            likes = (
                likes_summary.get("totalLikes")
                or likes_summary.get("aggregatedTotalLikes")
                or 0
            )
            comments = (
                comments_summary.get("totalFirstLevelComments")
                or comments_summary.get("aggregatedTotalComments")
                or 0
            )
        views = 0
        total = likes + comments
        return {
            "linkedin_id": post_id,
            "views": views,
            "likes": likes,
            "replies": comments,
            "comments": comments,
            "reposts": 0,
            "quotes": 0,
            "engagement_rate": (total / views) if views > 0 else 0.0,
        }

    async def get_user_posts(self, limit: int = 25) -> list[dict]:
        logger.warning("LinkedIn get_user_posts not implemented; returning []")
        return []

    def set_access_token(self, token: str) -> None:
        self.access_token = token

    async def close(self) -> None:
        await self._client.aclose()


def get_linkedin_client(settings: Settings) -> LinkedInClient:
    if settings.is_production:
        if not settings.linkedin_access_token:
            raise ValueError(LINKEDIN_ACCESS_TOKEN_REQUIRED)
        if not settings.linkedin_author_urn:
            raise ValueError(LINKEDIN_AUTHOR_URN_REQUIRED)
        return RealLinkedInClient(
            access_token=settings.linkedin_access_token,
            author_urn=settings.linkedin_author_urn,
            linkedin_version=settings.linkedin_version,
        )
    return MockLinkedInClient()
