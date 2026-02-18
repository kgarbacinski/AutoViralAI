"""Health check script.

Usage:
    uv run python scripts/check_health.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from src.persistence import create_store
from src.store.knowledge_base import KnowledgeBase
from src.tools.threads_api import get_threads_client


async def main():
    settings = get_settings()
    print(f"Environment: {settings.env}")
    print(f"Account ID: {settings.account_id}")
    print(f"Target followers: {settings.target_followers}")
    print()

    # Check store
    store = create_store(settings)
    kb = KnowledgeBase(store=store, account_id=settings.account_id)

    niche = await kb.get_niche_config()
    print(f"Niche config: {'loaded' if niche else 'NOT FOUND'}")

    strategy = await kb.get_strategy()
    print(f"Strategy: iteration {strategy.iteration}")
    print(f"  Learnings: {len(strategy.key_learnings)}")

    posts = await kb.get_recent_posts()
    print(f"Published posts: {len(posts)}")

    pending = await kb.get_pending_metrics_posts()
    print(f"Pending metrics: {len(pending)}")

    performances = await kb.get_all_pattern_performances()
    print(f"Pattern performances: {len(performances)}")

    # Check Threads client
    threads = get_threads_client(settings)
    print(f"\nThreads client: {type(threads).__name__}")
    try:
        followers = await threads.get_follower_count()
        print(f"Follower count: {followers}")
    except Exception as e:
        print(f"Follower count: ERROR - {e}")

    print("\nHealth check complete.")


if __name__ == "__main__":
    asyncio.run(main())
