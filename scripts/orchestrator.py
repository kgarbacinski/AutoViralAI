"""Orchestrator - schedules creation and learning pipeline runs."""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langgraph.types import Command

from config.settings import Settings, get_settings
from src.graphs.creation_pipeline import build_creation_pipeline
from src.graphs.learning_pipeline import build_learning_pipeline
from src.persistence import create_checkpointer, create_store

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Manages scheduling and execution of both pipelines."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.store = create_store(self.settings)
        self.checkpointer = create_checkpointer(self.settings)
        self._scheduler = AsyncIOScheduler()
        self._creation_cycle = 0
        self._learning_cycle = 0

    def setup_schedules(self) -> None:
        """Configure APScheduler jobs for both pipelines."""
        for hour in [8, 12, 18]:
            self._scheduler.add_job(
                self.run_creation_pipeline,
                "cron",
                hour=hour,
                minute=0,
                timezone="Europe/Warsaw",
                id=f"creation_{hour}",
                replace_existing=True,
            )

        self._scheduler.add_job(
            self.run_learning_pipeline,
            "cron",
            hour=6,
            minute=0,
            timezone="Europe/Warsaw",
            id="learning",
            replace_existing=True,
        )

    async def run_creation_pipeline(self) -> dict | None:
        """Execute a single creation pipeline cycle."""
        self._creation_cycle += 1
        logger.info(f"Starting creation pipeline cycle #{self._creation_cycle}")

        graph = build_creation_pipeline(self.settings, self.store)
        compiled = graph.compile(checkpointer=self.checkpointer)

        config = {
            "configurable": {
                "thread_id": f"creation_{self._creation_cycle}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            }
        }

        initial_state = {
            "current_follower_count": 0,
            "target_follower_count": self.settings.target_followers,
            "goal_reached": False,
            "viral_posts": [],
            "extracted_patterns": [],
            "generated_variants": [],
            "ranked_posts": [],
            "selected_post": None,
            "human_decision": None,
            "human_edited_content": None,
            "human_feedback": None,
            "published_post": None,
            "cycle_number": self._creation_cycle,
            "errors": [],
        }

        try:
            result = None
            async for event in compiled.astream(initial_state, config):
                result = event
                logger.info(f"Creation pipeline event: {list(event.keys())}")

            logger.info(f"Creation pipeline cycle #{self._creation_cycle} completed")
            return result
        except Exception as e:
            logger.error(f"Creation pipeline cycle #{self._creation_cycle} failed: {e}")
            raise

    async def run_learning_pipeline(self) -> dict | None:
        """Execute a single learning pipeline cycle."""
        self._learning_cycle += 1
        logger.info(f"Starting learning pipeline cycle #{self._learning_cycle}")

        graph = build_learning_pipeline(self.settings, self.store)
        compiled = graph.compile(checkpointer=self.checkpointer)

        config = {
            "configurable": {
                "thread_id": f"learning_{self._learning_cycle}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            }
        }

        initial_state = {
            "posts_to_check": [],
            "collected_metrics": [],
            "performance_analysis": None,
            "pattern_updates": [],
            "new_strategy": None,
            "cycle_number": self._learning_cycle,
            "errors": [],
        }

        try:
            result = None
            async for event in compiled.astream(initial_state, config):
                result = event
                logger.info(f"Learning pipeline event: {list(event.keys())}")

            logger.info(f"Learning pipeline cycle #{self._learning_cycle} completed")
            return result
        except Exception as e:
            logger.error(f"Learning pipeline cycle #{self._learning_cycle} failed: {e}")
            raise

    def start(self) -> None:
        """Start the scheduler."""
        self.setup_schedules()
        self._scheduler.start()
        logger.info("Orchestrator started with scheduled jobs")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._scheduler.shutdown()
        logger.info("Orchestrator stopped")
