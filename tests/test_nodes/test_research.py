"""Tests for research node."""

from unittest.mock import AsyncMock

import pytest

from src.models.research import ViralPost
from src.nodes.research import research_viral_content
from src.tools.apify_client import MockThreadsScraper


@pytest.fixture
def mock_hn():
    hn = AsyncMock()
    hn.get_viral_posts.return_value = [
        ViralPost(
            platform="hackernews",
            author="pg",
            content="Show HN: A new way to build web apps",
            url="https://news.ycombinator.com/item?id=1",
            likes=350,
            replies=120,
        ),
    ]
    return hn


@pytest.mark.asyncio
async def test_research_returns_posts(kb, sample_niche, mock_hn):
    await kb.save_niche_config(sample_niche)

    state = {"viral_posts": [], "errors": []}
    result = await research_viral_content(
        state,
        hn=mock_hn,
        scraper=MockThreadsScraper(),
        kb=kb,
    )

    assert len(result["viral_posts"]) > 0
    platforms = {p["platform"] for p in result["viral_posts"]}
    assert "hackernews" in platforms
    assert "threads" in platforms
