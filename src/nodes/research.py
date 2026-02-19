import asyncio
import hashlib

from src.models.state import CreationPipelineState
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import ThreadsScraper
from src.tools.hackernews_client import HackerNewsClient

DEFAULT_HASHTAGS = ["programming", "tech", "coding"]


async def research_viral_content(
    state: CreationPipelineState,
    *,
    hn: HackerNewsClient,
    scraper: ThreadsScraper,
    kb: KnowledgeBase,
) -> dict:
    niche_config = await kb.get_niche_config()

    all_posts = []
    errors = []

    hashtags = []
    if niche_config:
        hashtags = niche_config.hashtags_primary + niche_config.hashtags_secondary
    if not hashtags:
        hashtags = DEFAULT_HASHTAGS

    hn_result, threads_result = await asyncio.gather(
        hn.get_viral_posts(limit=30),
        scraper.scrape_viral_posts(hashtags=hashtags, limit=20),
        return_exceptions=True,
    )

    if isinstance(hn_result, Exception):
        errors.append(f"research: HackerNews fetch failed: {hn_result}")
    else:
        all_posts.extend([p.model_dump() for p in hn_result])

    if isinstance(threads_result, Exception):
        errors.append(f"research: Threads scraping failed: {threads_result}")
    else:
        all_posts.extend([p.model_dump() for p in threads_result])

    seen_hashes = set()
    unique_posts = []
    for post in all_posts:
        content = post.get("content", "")
        content_key = (
            hashlib.sha256(content.encode()).hexdigest()
            if content
            else f"_empty_{post.get('url', id(post))}"
        )
        if content_key not in seen_hashes:
            seen_hashes.add(content_key)
            unique_posts.append(post)

    result = {"viral_posts": unique_posts}
    if errors:
        result["errors"] = errors
    return result
