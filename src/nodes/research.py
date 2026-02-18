"""Research node - discovers viral content in the niche."""

from src.models.state import CreationPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import ThreadsScraper
from src.tools.hackernews_client import HackerNewsResearcher


async def research_viral_content(
    state: CreationPipelineState,
    *,
    hn: HackerNewsResearcher,
    scraper: ThreadsScraper,
    kb: KnowledgeBase,
) -> dict:
    """Search for viral posts across HackerNews and Threads."""
    niche_config = await kb.get_niche_config()

    all_posts = []

    # Source 1: Hacker News top/best stories
    try:
        hn_posts = await hn.get_viral_posts(limit=30)
        all_posts.extend([p.model_dump() for p in hn_posts])
    except Exception as e:
        return {
            "viral_posts": all_posts,
            "errors": [f"research: HackerNews fetch failed: {e}"],
        }

    # Source 2: Threads viral posts via Apify
    try:
        hashtags = []
        if niche_config:
            hashtags = niche_config.hashtags_primary + niche_config.hashtags_secondary
        if not hashtags:
            hashtags = ["programming", "tech", "coding"]
        threads_posts = await scraper.scrape_viral_posts(hashtags=hashtags, limit=20)
        all_posts.extend([p.model_dump() for p in threads_posts])
    except Exception as e:
        return {
            "viral_posts": all_posts,
            "errors": [f"research: Threads scraping failed: {e}"],
        }

    # Deduplicate
    seen_contents = set()
    unique_posts = []
    for post in all_posts:
        content_key = post["content"][:100]
        if content_key not in seen_contents:
            seen_contents.add(content_key)
            unique_posts.append(post)

    return {"viral_posts": unique_posts}
