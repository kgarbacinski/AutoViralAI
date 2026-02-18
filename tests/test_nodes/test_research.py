"""Tests for research node."""

import pytest

from src.nodes.research import research_viral_content
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import MockThreadsScraper
from src.tools.reddit_client import MockRedditResearcher


@pytest.mark.asyncio
async def test_research_returns_posts(kb, sample_niche):
    await kb.save_niche_config(sample_niche)

    state = {"viral_posts": [], "errors": []}
    result = await research_viral_content(
        state,
        reddit=MockRedditResearcher(),
        scraper=MockThreadsScraper(),
        kb=kb,
    )

    assert len(result["viral_posts"]) > 0
    # Should have posts from both platforms
    platforms = {p["platform"] for p in result["viral_posts"]}
    assert "reddit" in platforms
    assert "threads" in platforms
