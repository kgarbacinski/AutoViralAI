"""Status command handler for Telegram bot."""

import logging
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from bot.dependencies import get_knowledge_base, get_orchestrator

logger = logging.getLogger(__name__)


async def handle_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show live agent status."""
    orchestrator = get_orchestrator()
    kb = get_knowledge_base()

    lines = ["🤖 <b>AutoViralAI Status</b>\n"]

    if orchestrator:
        if orchestrator.is_paused:
            state = "🟡 Paused"
        else:
            state = "🟢 Running"
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

        # Next scheduled run
        jobs = orchestrator.get_scheduled_jobs()
        next_runs = [
            j["next_run_time"] for j in jobs if j.get("next_run_time") and not j.get("paused")
        ]
        if next_runs:
            lines.append(f"⏰ Next run: {next_runs[0]}")
    else:
        lines.append("State: Orchestrator not available")

    # Strategy iteration
    if kb:
        try:
            strategy = await kb.get_strategy()
            lines.append(f"\n🧠 Strategy iteration: {strategy.iteration}")
            if strategy.last_updated:
                lines.append(f"Last updated: {strategy.last_updated[:16]}")
        except Exception as e:
            logger.error(f"Error fetching strategy for status: {e}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
