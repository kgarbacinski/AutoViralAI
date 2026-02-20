import logging
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from bot.dependencies import get_knowledge_base, get_orchestrator
from bot.messages import (
    STATUS_HEADER,
    STATUS_ORCHESTRATOR_UNAVAILABLE,
    STATUS_PAUSED,
    STATUS_RUNNING,
)
from src.exceptions import KnowledgeBaseError

logger = logging.getLogger(__name__)


async def handle_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    kb = get_knowledge_base()

    lines = [STATUS_HEADER]

    if orchestrator:
        state = STATUS_PAUSED if orchestrator.is_paused else STATUS_RUNNING
        lines.append(f"State: {state}")
        lines.append(
            f"📋 Cycles: {orchestrator.creation_cycle} creation, "
            f"{orchestrator.learning_cycle} learning"
        )

        pending = orchestrator.pending_approvals
        if pending:
            lines.append(f"⏳ Pending approvals: {len(pending)}")
            for tid in pending:
                lines.append(f"  • {escape(tid)}")
        else:
            lines.append("Pending approvals: 0")

        jobs = orchestrator.get_scheduled_jobs()
        next_runs = [
            j["next_run_time"] for j in jobs if j.get("next_run_time") and not j.get("paused")
        ]
        if next_runs:
            lines.append(f"⏰ Next run: {next_runs[0]}")
    else:
        lines.append(STATUS_ORCHESTRATOR_UNAVAILABLE)

    if kb:
        try:
            strategy = await kb.get_strategy()
            lines.append(f"\n🧠 Strategy iteration: {strategy.iteration}")
            if strategy.last_updated:
                lines.append(f"Last updated: {strategy.last_updated[:16]}")
        except KnowledgeBaseError as e:
            logger.error("Error fetching strategy for status: %s", e)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
