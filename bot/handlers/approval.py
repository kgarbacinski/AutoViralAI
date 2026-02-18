"""Telegram callback handlers for post approval."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_pending_resumes: dict[str, dict] = {}


def register_pending_resume(thread_id: str, graph_config: dict) -> None:
    """Register a graph interrupt waiting for human decision."""
    _pending_resumes[thread_id] = graph_config


def get_pending_resume(thread_id: str) -> dict | None:
    """Get the graph config for a pending resume."""
    return _pending_resumes.get(thread_id)


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
        await _resume_graph(thread_id, decision, context)


async def _resume_graph(thread_id: str, decision: dict, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume the paused graph with the human's decision."""
    graph_config = get_pending_resume(thread_id)
    if not graph_config:
        logger.warning(f"No pending resume found for thread_id={thread_id}")
        return

    graph_config["decision"] = decision
    _pending_resumes[thread_id] = graph_config

    logger.info(f"Decision stored for thread_id={thread_id}: {decision}")
