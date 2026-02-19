from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from apify_client import ApifyClientAsync

from src.models.research import ViralPost

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

APIFY_TIMEOUT_SECS = 120


class ThreadsScraper(ABC):
    @abstractmethod
    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]: ...

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


class MockThreadsScraper(ThreadsScraper):
    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]:
        return [
            ViralPost(
                platform="threads",
                author="@techbro",
                content=(
                    "Python in 2025:\n\n- uv replaced pip\n- Pydantic replaced dataclasses\n"
                    "- FastAPI replaced Flask\n- Ruff replaced black+isort+flake8\n\n"
                    "The ecosystem moves fast. Adapt or get left behind."
                ),
                likes=12500,
                replies=890,
                reposts=3200,
                views=450000,
                engagement_rate=0.037,
                topic_tags=["python", "tools"],
            ),
            ViralPost(
                platform="threads",
                author="@devinsights",
                content=(
                    "Stop saying 'I'm not a real developer because I use AI tools.'\n\n"
                    "Pilots use autopilot.\nDoctors use diagnostic AI.\n"
                    "Accountants use calculators.\n\n"
                    "Using tools doesn't make you less skilled. It makes you more effective."
                ),
                likes=28900,
                replies=2100,
                reposts=8400,
                views=1200000,
                engagement_rate=0.033,
                topic_tags=["ai", "career"],
            ),
            ViralPost(
                platform="threads",
                author="@startuplessons",
                content=(
                    "My side project made $0 for 11 months.\n\n"
                    "Month 12: $47\nMonth 13: $340\nMonth 14: $1,200\nMonth 18: $8,500/mo\n\n"
                    "The growth was never linear. Most people quit during the $0 months.\n\n"
                    "Don't be most people."
                ),
                likes=45000,
                replies=3400,
                reposts=12000,
                views=2000000,
                engagement_rate=0.030,
                topic_tags=["startup", "motivation"],
            ),
        ]


class RealThreadsScraper(ThreadsScraper):
    def __init__(self, api_token: str):
        self.client = ApifyClientAsync(api_token)

    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]:
        run_input = {
            "hashtags": hashtags,
            "resultsLimit": limit,
            "sortBy": "popular",
        }
        logger.info("Starting Apify Threads scraper (timeout=%ds)", APIFY_TIMEOUT_SECS)
        try:
            run = await self.client.actor("apify/threads-scraper").call(
                run_input=run_input,
                timeout_secs=APIFY_TIMEOUT_SECS,
            )
        except Exception:
            logger.exception("Apify actor call failed")
            return []

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            logger.error("Apify run did not return a dataset ID")
            return []

        items = []
        try:
            async for item in self.client.dataset(dataset_id).iterate_items():
                items.append(
                    ViralPost(
                        platform="threads",
                        author=item.get("author", {}).get("username", "unknown"),
                        content=item.get("text", ""),
                        url=item.get("url", ""),
                        likes=item.get("likes", 0),
                        replies=item.get("replies", 0),
                        reposts=item.get("reposts", 0),
                        views=item.get("views", 0),
                        engagement_rate=0.0,
                        topic_tags=[],
                    )
                )
        except Exception:
            logger.exception(
                "Failed to iterate Apify dataset items (collected %d items before failure)",
                len(items),
            )

        logger.info("Apify scraper returned %d items", len(items))
        return items

    async def close(self) -> None:
        if hasattr(self.client, "_http_client"):
            await self.client._http_client.aclose()


def get_threads_scraper(settings: Settings) -> ThreadsScraper:
    if settings.is_production:
        if not settings.apify_api_token:
            raise ValueError(
                "APIFY_API_TOKEN is required in production. "
                "Get it from https://console.apify.com/account/integrations"
            )
        return RealThreadsScraper(api_token=settings.apify_api_token)
    return MockThreadsScraper()
