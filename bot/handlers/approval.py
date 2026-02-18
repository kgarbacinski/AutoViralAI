"""Telegram callback handlers for post approval."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_orchestrator = None


def set_orchestrator(orchestrator) -> None:
    """Set the orchestrator instance for graph resumption."""
    global _orchestrator
    _orchestrator = orchestrator


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks for Approve/Edit/Reject."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split(":")

    if len(parts) < 2:
        await query.edit_message_text("Invalid callback data.")
        return

    action = parts[0]
    thread_id = parts[1]

    if action == "approve":
        decision = {"decision": "approve"}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- APPROVED ---",
        )

    elif action == "reject":
        decision = {"decision": "reject", "feedback": "Rejected by human"}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- REJECTED ---",
        )

    elif action == "edit":
        # Ask user to send edited version
        decision = None
        await query.edit_message_text(
            f"{query.message.text}\n\n--- EDIT MODE ---\n"
            "Please send the edited post text as a reply.",
        )
        context.user_data["awaiting_edit"] = thread_id
        return

    elif action == "alt":
        alt_index = int(parts[2]) if len(parts) > 2 else 0
        decision = {"decision": "approve", "use_alternative": alt_index}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- APPROVED (Alt {alt_index + 1}) ---",
        )

    else:
        await query.edit_message_text("Unknown action.")
        return

    if decision:
        await _resume_graph(thread_id, decision)


async def handle_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages — used when user sends edited post content after clicking Edit."""
    thread_id = context.user_data.get("awaiting_edit")
    if not thread_id:
        return

    edited_content = update.message.text.strip()
    del context.user_data["awaiting_edit"]

    await update.message.reply_text("Edited post received. Publishing...")

    decision = {"decision": "edit", "edited_content": edited_content}
    await _resume_graph(thread_id, decision)


async def _resume_graph(thread_id: str, decision: dict) -> None:
    """Resume the paused graph with the human's decision via the orchestrator."""
    if _orchestrator is None:
        logger.error("Orchestrator not set — cannot resume graph")
        return

    try:
        await _orchestrator.resume_creation(thread_id, decision)
        logger.info(f"Graph resumed for thread_id={thread_id} with decision={decision}")
    except Exception as e:
        logger.error(f"Failed to resume graph for thread_id={thread_id}: {e}")
