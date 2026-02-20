# Usage: uv run python scripts/init_account.py

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from scripts.manual_run import init_niche_config
from src.persistence import create_store
from src.store.knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()
    store = create_store(settings)
    kb = KnowledgeBase(store=store, account_id=settings.account_id)

    await init_niche_config(kb)

    niche = await kb.get_niche_config()
    if niche:
        logger.info("Account initialized: %s / %s", niche.niche, niche.sub_niche)
        logger.info("Content pillars: %s", [p.name for p in niche.content_pillars])
        logger.info("Voice: %s", niche.voice.tone)
    else:
        logger.error("Failed to initialize account config")


if __name__ == "__main__":
    asyncio.run(main())
