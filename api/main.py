"""FastAPI application - webhook + status endpoints."""

import logging
from contextlib import AsyncExitStack, asynccontextmanager

import yaml
from fastapi import FastAPI

from api.routes.config import router as config_router
from api.routes.status import router as status_router
from bot.dependencies import set_authorized_chat_id, set_knowledge_base, set_orchestrator
from bot.handlers.commands import cancel_background_tasks
from bot.telegram_bot import create_bot
from bot.webhook import router as webhook_router, set_bot_app, set_webhook_secret
from config.settings import get_settings
from src.models.strategy import AccountNiche, AudienceConfig, ContentPillar, VoiceConfig
from src.orchestrator import PipelineOrchestrator
from src.persistence import (
    create_checkpointer,
    create_postgres_checkpointer,
    create_postgres_store,
    create_store,
)
from src.store.knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _init_niche_config(kb: KnowledgeBase) -> None:
    """Load niche config from YAML into the store if not already present."""
    existing = await kb.get_niche_config()
    if existing:
        logger.info("Niche config already in store, skipping init")
        return

    settings = get_settings()
    config_path = settings.niche_config_path

    raw = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}

    niche = AccountNiche(
        niche=raw.get("niche", "tech"),
        sub_niche=raw.get("sub_niche", "programming & startups"),
        description=raw.get("description", ""),
        voice=VoiceConfig(
            tone=raw.get("voice", {}).get("tone", "conversational"),
            persona=raw.get("voice", {}).get("persona", "tech expert"),
            style_notes=raw.get("voice", {}).get("style_notes", []),
        ),
        audience=AudienceConfig(
            primary=raw.get("audience", {}).get("primary", "developers"),
            secondary=raw.get("audience", {}).get("secondary", "tech enthusiasts"),
            pain_points=raw.get("audience", {}).get("pain_points", []),
        ),
        content_pillars=[
            ContentPillar(name=p["name"], description=p["description"], weight=p["weight"])
            for p in raw.get("content_pillars", [])
        ],
        avoid_topics=raw.get("avoid_topics", []),
        hashtags_primary=raw.get("hashtags", {}).get("primary", []),
        hashtags_secondary=raw.get("hashtags", {}).get("secondary", []),
        max_hashtags_per_post=raw.get("hashtags", {}).get("max_per_post", 3),
        posting_timezone=raw.get("posting_schedule", {}).get("timezone", "Europe/Warsaw"),
        preferred_posting_times=raw.get("posting_schedule", {}).get("preferred_times", []),
        max_posts_per_day=raw.get("posting_schedule", {}).get("max_posts_per_day", 3),
    )

    await kb.save_niche_config(niche)
    logger.info("Niche config initialized in store from YAML")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    settings = get_settings()
    logger.info(f"Starting agent in {settings.env} mode")

    async with AsyncExitStack() as exit_stack:
        # 1. Persistence setup
        if settings.is_production and not settings.postgres_uri:
            raise RuntimeError("POSTGRES_URI is required in production mode")
        if settings.is_production:
            store = await exit_stack.enter_async_context(
                create_postgres_store(settings.postgres_uri)
            )
            checkpointer = await exit_stack.enter_async_context(
                create_postgres_checkpointer(settings.postgres_uri)
            )
            logger.info("Postgres store and checkpointer tables created")
        else:
            store = create_store(settings)
            checkpointer = create_checkpointer(settings)

        # 2. Niche config → Knowledge Base
        kb = KnowledgeBase(store=store, account_id=settings.account_id)
        set_knowledge_base(kb)
        await _init_niche_config(kb)

        # 3. Telegram bot
        bot_app = None
        if settings.telegram_chat_id:
            set_authorized_chat_id(settings.telegram_chat_id)
        if settings.telegram_bot_token:
            bot_app = create_bot(settings.telegram_bot_token, settings.telegram_chat_id)
            await bot_app.initialize()
            set_bot_app(bot_app)
            logger.info("Telegram bot initialized")

            if settings.telegram_webhook_url:
                webhook_url = f"{settings.telegram_webhook_url.rstrip('/')}/webhook/telegram"
                webhook_kwargs = {"url": webhook_url}
                if settings.telegram_webhook_secret:
                    webhook_kwargs["secret_token"] = settings.telegram_webhook_secret
                    set_webhook_secret(settings.telegram_webhook_secret)
                await bot_app.bot.set_webhook(**webhook_kwargs)
                logger.info(f"Telegram webhook set to {webhook_url}")
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not set — bot disabled")

        # 4. Orchestrator
        orchestrator = PipelineOrchestrator(
            settings=settings,
            store=store,
            checkpointer=checkpointer,
            bot_app=bot_app,
            telegram_chat_id=settings.telegram_chat_id,
        )
        set_orchestrator(orchestrator)
        orchestrator.start()

        # Expose on app.state for status endpoint
        app.state.orchestrator = orchestrator

        logger.info("Agent fully started")

        yield

        # Shutdown
        logger.info("Shutting down agent...")
        await cancel_background_tasks()
        await orchestrator.stop()

        if bot_app:
            await bot_app.shutdown()
            logger.info("Telegram bot shut down")

        logger.info("Agent stopped")


app = FastAPI(
    title="AutoViralAI API",
    description="API for the autonomous viral content growth agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router, tags=["telegram"])
app.include_router(status_router, prefix="/api", tags=["status"])
app.include_router(config_router, prefix="/api", tags=["config"])


@app.get("/health")
async def health():
    return {"status": "ok"}
