import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langgraph.types import Command

from bot.telegram_bot import build_enrichment_data, send_approval_request, send_pipeline_report
from config.settings import Settings, get_settings
from src.graphs.creation_pipeline import build_creation_pipeline
from src.graphs.learning_pipeline import build_learning_pipeline
from src.persistence import create_checkpointer, create_store
from src.store.knowledge_base import KnowledgeBase
from src.tools.apify_client import get_threads_scraper
from src.tools.embeddings import EmbeddingClient
from src.tools.hackernews_client import get_hackernews_client
from src.tools.threads_api import get_threads_client

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
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
        self._cycle_lock = asyncio.Lock()
        self._pending_interrupts: dict[str, dict] = {}
        self._paused = False
        self.kb = KnowledgeBase(store=self.store, account_id=self.settings.account_id)

        self._threads_client = get_threads_client(self.settings)
        self._hn_client = get_hackernews_client(self.settings)
        self._scraper = get_threads_scraper(self.settings)
        self._embedding_client = EmbeddingClient()

    def setup_schedules(self) -> None:
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
        async with self._cycle_lock:
            self._creation_cycle += 1
            cycle = self._creation_cycle

        logger.info("Starting creation pipeline cycle #%d", cycle)

        graph = build_creation_pipeline(
            self.settings,
            self.store,
            threads_client=self._threads_client,
            hn=self._hn_client,
            scraper=self._scraper,
            embedding_client=self._embedding_client,
        )
        compiled = graph.compile(checkpointer=self.checkpointer)

        thread_id = f"creation_{cycle}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
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
            "cycle_number": cycle,
            "errors": [],
        }

        try:
            result = None
            async for event in compiled.astream(initial_state, config):
                result = event
                logger.info("Creation pipeline event: %s", list(event.keys()))

            state = await compiled.aget_state(config)
            if state.next and "human_approval" in state.next:
                logger.info(
                    "Creation cycle #%d paused at human_approval (thread=%s)",
                    cycle,
                    thread_id,
                )
                self._pending_interrupts[thread_id] = {
                    "compiled": compiled,
                    "config": config,
                }
                await self._send_approval_telegram(thread_id, state)
                return result

            logger.info("Creation pipeline cycle #%d completed", cycle)
            return result
        except Exception as e:
            logger.error("Creation pipeline cycle #%d failed: %s", cycle, e)
            raise

    async def _send_approval_telegram(self, thread_id: str, state) -> None:
        if not self.bot_app or not self.telegram_chat_id:
            logger.warning("Cannot send approval request: bot_app or chat_id not configured")
            return

        values = state.values
        selected_post = values.get("selected_post", {})
        ranked_posts = values.get("ranked_posts", [])
        alternatives = ranked_posts[1:3] if len(ranked_posts) > 1 else []

        try:
            await send_pipeline_report(self.bot_app, self.telegram_chat_id, values)
        except Exception as e:
            logger.error("Failed to send pipeline report: %s", e)

        enrichment = None
        try:
            enrichment = await build_enrichment_data(self.kb, selected_post or {})
        except Exception as e:
            logger.error("Failed to build enrichment data: %s", e)

        try:
            await send_approval_request(
                app=self.bot_app,
                chat_id=self.telegram_chat_id,
                thread_id=thread_id,
                selected_post=selected_post or {},
                alternatives=alternatives,
                cycle_number=values.get("cycle_number", 0),
                follower_count=values.get("current_follower_count", 0),
                enrichment=enrichment,
            )
            logger.info("Approval request sent to Telegram for thread=%s", thread_id)
        except Exception as e:
            logger.error("Failed to send Telegram approval: %s", e)

    async def resume_creation(self, thread_id: str, decision: dict) -> dict | None:
        pending = self._pending_interrupts.pop(thread_id, None)
        if not pending:
            logger.info(
                "No in-memory interrupt for %s, reconstructing from checkpointer", thread_id
            )
            graph = build_creation_pipeline(
                self.settings,
                self.store,
                threads_client=self._threads_client,
                hn=self._hn_client,
                scraper=self._scraper,
                embedding_client=self._embedding_client,
            )
            compiled = graph.compile(checkpointer=self.checkpointer)
            config = {"configurable": {"thread_id": thread_id}}

            try:
                state = await compiled.aget_state(config)
            except Exception as e:
                logger.error("Failed to get state for thread_id=%s: %s", thread_id, e)
                return None

            if not (state and state.next and "human_approval" in state.next):
                logger.warning(
                    "Thread %s not paused at human_approval (next=%s)",
                    thread_id,
                    state.next if state else None,
                )
                return None

            pending = {"compiled": compiled, "config": config}

        compiled = pending["compiled"]
        config = pending["config"]

        publish_at = decision.get("publish_at")
        if publish_at:
            self._pending_interrupts[thread_id] = pending
            self._schedule_delayed_publish(thread_id, decision, publish_at)
            return None

        logger.info("Resuming creation pipeline thread=%s with decision=%s", thread_id, decision)

        try:
            result = None
            async for event in compiled.astream(Command(resume=decision), config):
                result = event
                logger.info("Resume event: %s", list(event.keys()))

            state = await compiled.aget_state(config)
            if state.next and "human_approval" in state.next:
                logger.info("Another interrupt detected after resume (thread=%s)", thread_id)
                self._pending_interrupts[thread_id] = {
                    "compiled": compiled,
                    "config": config,
                }
                await self._send_approval_telegram(thread_id, state)
                return result

            logger.info("Creation pipeline thread=%s completed after resume", thread_id)
            return result
        except Exception as e:
            logger.error("Failed to resume creation pipeline thread=%s: %s", thread_id, e)
            raise

    def _schedule_delayed_publish(self, thread_id: str, decision: dict, publish_at: str) -> None:
        try:
            run_date = datetime.fromisoformat(publish_at)
        except ValueError:
            logger.error("Invalid publish_at datetime: %s", publish_at)
            return

        if run_date.tzinfo is None:
            run_date = run_date.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        if run_date <= now:
            logger.warning(
                "publish_at %s is in the past — scheduling for immediate execution",
                publish_at,
            )

        resume_decision = {k: v for k, v in decision.items() if k != "publish_at"}

        async def _delayed_resume():
            try:
                await self.resume_creation(thread_id, resume_decision)
            except Exception:
                logger.exception("Delayed publish failed for thread=%s", thread_id)

        self._scheduler.add_job(
            _delayed_resume,
            "date",
            run_date=run_date,
            id=f"delayed_publish_{thread_id}",
            replace_existing=True,
        )
        # TODO: APScheduler uses in-memory job store — delayed publishes are lost on restart.
        # Consider a persistent job store (e.g. Redis/PostgreSQL) for production reliability.
        logger.info("Scheduled delayed publish for thread=%s at %s", thread_id, publish_at)

    async def run_learning_pipeline(self) -> dict | None:
        async with self._cycle_lock:
            self._learning_cycle += 1
            cycle = self._learning_cycle

        logger.info("Starting learning pipeline cycle #%d", cycle)

        graph = build_learning_pipeline(
            self.settings,
            self.store,
            threads_client=self._threads_client,
        )
        compiled = graph.compile(checkpointer=self.checkpointer)

        config = {
            "configurable": {
                "thread_id": f"learning_{cycle}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            }
        }

        initial_state = {
            "posts_to_check": [],
            "collected_metrics": [],
            "performance_analysis": None,
            "pattern_updates": [],
            "new_strategy": None,
            "cycle_number": cycle,
            "errors": [],
        }

        try:
            result = None
            async for event in compiled.astream(initial_state, config):
                result = event
                logger.info("Learning pipeline event: %s", list(event.keys()))

            logger.info("Learning pipeline cycle #%d completed", cycle)
            return result
        except Exception as e:
            logger.error("Learning pipeline cycle #%d failed: %s", cycle, e)
            raise

    async def run_research_only(self) -> list[dict]:
        from src.nodes.research import research_viral_content

        minimal_state = {
            "viral_posts": [],
            "errors": [],
        }

        result = await research_viral_content(
            minimal_state, hn=self._hn_client, scraper=self._scraper, kb=self.kb
        )
        return result.get("viral_posts", [])

    @property
    def pending_approvals(self) -> dict[str, dict]:
        return dict(self._pending_interrupts)

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def creation_cycle(self) -> int:
        return self._creation_cycle

    @property
    def learning_cycle(self) -> int:
        return self._learning_cycle

    def get_scheduled_jobs(self) -> list[dict]:
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "paused": job.next_run_time is None,
                }
            )
        return jobs

    def pause_all_jobs(self) -> None:
        for job in self._scheduler.get_jobs():
            job.pause()
        self._paused = True
        logger.info("All scheduled jobs paused")

    def resume_all_jobs(self) -> None:
        for job in self._scheduler.get_jobs():
            job.resume()
        self._paused = False
        logger.info("All scheduled jobs resumed")

    def reschedule_creation_jobs(self, posting_times: list[str]) -> None:
        for job in self._scheduler.get_jobs():
            if job.id.startswith("creation_"):
                job.remove()

        for time_str in posting_times:
            parts = time_str.split(":")
            try:
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                logger.warning("Skipping invalid posting time: %s", time_str)
                continue
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                logger.warning("Skipping out-of-range posting time: %s", time_str)
                continue
            self._scheduler.add_job(
                self.run_creation_pipeline,
                "cron",
                hour=hour,
                minute=minute,
                timezone="Europe/Warsaw",
                id=f"creation_{hour}_{minute:02d}",
                replace_existing=True,
            )

        logger.info("Rescheduled creation jobs for times: %s", posting_times)

    def start(self) -> None:
        self.setup_schedules()
        self._scheduler.start()
        logger.info("Orchestrator started with scheduled jobs")

    async def stop(self) -> None:
        self._scheduler.shutdown()
        for client in (self._threads_client, self._hn_client, self._scraper):
            try:
                await client.close()
            except Exception:
                logger.exception("Error closing %s", type(client).__name__)
        logger.info("Orchestrator stopped")
