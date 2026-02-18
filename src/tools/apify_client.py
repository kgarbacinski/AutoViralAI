"""Apify wrapper for scraping Threads viral content."""

from abc import ABC, abstractmethod

from apify_client import ApifyClientAsync

from src.models.research import ViralPost


class ThreadsScraper(ABC):
    @abstractmethod
    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]: ...


class MockThreadsScraper(ThreadsScraper):
    """Mock scraper returning sample Threads viral posts."""

    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]:
        return [
            ViralPost(
                platform="threads",
                author="@techbro",
                content="Python in 2025:\n\n- uv replaced pip\n- Pydantic replaced dataclasses\n- FastAPI replaced Flask\n- Ruff replaced black+isort+flake8\n\nThe ecosystem moves fast. Adapt or get left behind.",
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
                content="Stop saying 'I'm not a real developer because I use AI tools.'\n\nPilots use autopilot.\nDoctors use diagnostic AI.\nAccountants use calculators.\n\nUsing tools doesn't make you less skilled. It makes you more effective.",
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
                content="My side project made $0 for 11 months.\n\nMonth 12: $47\nMonth 13: $340\nMonth 14: $1,200\nMonth 18: $8,500/mo\n\nThe growth was never linear. Most people quit during the $0 months.\n\nDon't be most people.",
                likes=45000,
                replies=3400,
                reposts=12000,
                views=2000000,
                engagement_rate=0.030,
                topic_tags=["startup", "motivation"],
            ),
        ]


class RealThreadsScraper(ThreadsScraper):
    """Real Apify-based Threads scraper."""

    def __init__(self, api_token: str):
        self.client = ApifyClientAsync(api_token)

    async def scrape_viral_posts(self, hashtags: list[str], limit: int = 20) -> list[ViralPost]:
        run_input = {
            "hashtags": hashtags,
            "resultsLimit": limit,
            "sortBy": "popular",
        }
        run = await self.client.actor("apify/threads-scraper").call(run_input=run_input)
        items = []
        async for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
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
        return items


def get_threads_scraper(settings) -> ThreadsScraper:
    """Factory: returns real scraper in production, mock in development."""
    if settings.is_production:
        if not settings.apify_api_token:
            raise ValueError(
                "APIFY_API_TOKEN is required in production. "
                "Get it from https://console.apify.com/account/integrations"
            )
        return RealThreadsScraper(api_token=settings.apify_api_token)
    return MockThreadsScraper()
