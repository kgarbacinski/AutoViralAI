"""Orchestrator - schedules creation and learning pipeline runs."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langgraph.types import Command

from bot.telegram_bot import send_approval_request
from config.settings import Settings, get_settings
from src.graphs.creation_pipeline import build_creation_pipeline
from src.graphs.learning_pipeline import build_learning_pipeline
from src.persistence import create_checkpointer, create_store

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Manages scheduling and execution of both pipelines."""

    def __init__(
        self,
        settings: Settings | None = None,
        store=None,
        checkpointer=None,
        bot_app=None,
        telegram_chat_id: str = "",
    ):
        self.settings = settings or get_settings()
        self.store = store or create_store(self.settings)
        self.checkpointer = checkpointer or create_checkpointer(self.settings)
        self.bot_app = bot_app
        self.telegram_chat_id = telegram_chat_id or self.settings.telegram_chat_id
        self._scheduler = AsyncIOScheduler()
        self._creation_cycle = 0
        self._learning_cycle = 0
        # thread_id -> {"compiled": graph, "config": config, "state_snapshot": state}
        self._pending_interrupts: dict[str, dict] = {}

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

        thread_id = f"creation_{self._creation_cycle}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}

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

            # Check if graph paused at an interrupt (human_approval)
            state = await compiled.aget_state(config)
            if state.next and "human_approval" in state.next:
                logger.info(
                    f"Creation cycle #{self._creation_cycle} paused at human_approval (thread={thread_id})"
                )
                self._pending_interrupts[thread_id] = {
                    "compiled": compiled,
                    "config": config,
                }
                await self._send_approval_telegram(thread_id, state)
                return result

            logger.info(f"Creation pipeline cycle #{self._creation_cycle} completed")
            return result
        except Exception as e:
            logger.error(f"Creation pipeline cycle #{self._creation_cycle} failed: {e}")
            raise

    async def _send_approval_telegram(self, thread_id: str, state) -> None:
        """Send a Telegram message with approval buttons for a paused graph."""
        if not self.bot_app or not self.telegram_chat_id:
            logger.warning("Cannot send approval request: bot_app or chat_id not configured")
            return

        values = state.values
        selected_post = values.get("selected_post", {})
        ranked_posts = values.get("ranked_posts", [])
        alternatives = ranked_posts[1:3] if len(ranked_posts) > 1 else []

        try:
            await send_approval_request(
                app=self.bot_app,
                chat_id=self.telegram_chat_id,
                thread_id=thread_id,
                selected_post=selected_post or {},
                alternatives=alternatives,
                cycle_number=values.get("cycle_number", 0),
                follower_count=values.get("current_follower_count", 0),
            )
            logger.info(f"Approval request sent to Telegram for thread={thread_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram approval: {e}")

    async def resume_creation(self, thread_id: str, decision: dict) -> dict | None:
        """Resume a paused creation pipeline with the human's decision.

        Handles recursive interrupts (e.g., reject → regenerate → new interrupt).
        """
        pending = self._pending_interrupts.pop(thread_id, None)
        if not pending:
            logger.warning(f"No pending interrupt for thread_id={thread_id}")
            return None

        compiled = pending["compiled"]
        config = pending["config"]

        logger.info(f"Resuming creation pipeline thread={thread_id} with decision={decision}")

        try:
            result = None
            async for event in compiled.astream(Command(resume=decision), config):
                result = event
                logger.info(f"Resume event: {list(event.keys())}")

            # Check if another interrupt was triggered (reject → regenerate → new approval)
            state = await compiled.aget_state(config)
            if state.next and "human_approval" in state.next:
                logger.info(f"Another interrupt detected after resume (thread={thread_id})")
                self._pending_interrupts[thread_id] = {
                    "compiled": compiled,
                    "config": config,
                }
                await self._send_approval_telegram(thread_id, state)
                return result

            logger.info(f"Creation pipeline thread={thread_id} completed after resume")
            return result
        except Exception as e:
            logger.error(f"Failed to resume creation pipeline thread={thread_id}: {e}")
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

    @property
    def pending_approvals(self) -> dict[str, dict]:
        """Return pending interrupt thread IDs (for status endpoint)."""
        return dict(self._pending_interrupts)

    def get_scheduled_jobs(self) -> list[dict]:
        """Return info about scheduled jobs."""
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            })
        return jobs

    def start(self) -> None:
        """Start the scheduler."""
        self.setup_schedules()
        self._scheduler.start()
        logger.info("Orchestrator started with scheduled jobs")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._scheduler.shutdown()
        logger.info("Orchestrator stopped")
