"""Research node - discovers viral content in the niche."""

from src.models.state import CreationPipelineState
from src.models.strategy import AccountNiche, ContentStrategy
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import ThreadsScraper
from src.tools.reddit_client import RedditResearcher


async def research_viral_content(
    state: CreationPipelineState,
    *,
    reddit: RedditResearcher,
    scraper: ThreadsScraper,
    kb: KnowledgeBase,
) -> dict:
    """Search for viral posts across platforms relevant to our niche."""
    niche_config = await kb.get_niche_config()
    strategy = await kb.get_strategy()

    subreddits = ["programming", "webdev", "cscareerquestions", "startups", "technology"]
    search_queries = _build_search_queries(niche_config, strategy)

    all_posts = []

    for query in search_queries:
        try:
            reddit_posts = await reddit.search_viral_posts(
                subreddits=subreddits, query=query, limit=10
            )
            all_posts.extend([p.model_dump() for p in reddit_posts])
        except Exception as e:
            return {
                "viral_posts": all_posts,
                "errors": [f"research: Reddit search failed for '{query}': {e}"],
            }

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

    seen_contents = set()
    unique_posts = []
    for post in all_posts:
        content_key = post["content"][:100]
        if content_key not in seen_contents:
            seen_contents.add(content_key)
            unique_posts.append(post)

    return {"viral_posts": unique_posts}


def _build_search_queries(
    niche: AccountNiche | None, strategy: ContentStrategy | None
) -> list[str]:
    """Generate search queries based on niche config and current strategy."""
    base_queries = ["programming tips viral", "tech hot takes", "developer career advice"]

    if strategy and strategy.preferred_patterns:
        pattern_queries = {
            "contrarian_hot_take": "unpopular opinion programming",
            "numbered_list": "top things developers",
            "personal_story": "developer journey lessons learned",
            "stat_hook": "programming statistics surprising",
        }
        for pattern in strategy.preferred_patterns[:2]:
            if pattern in pattern_queries:
                base_queries.append(pattern_queries[pattern])

    return base_queries[:5]  # Limit to 5 queries to avoid rate limits
