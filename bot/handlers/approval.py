"""Telegram callback handlers for post approval."""

import logging
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.dependencies import get_authorized_chat_id, get_orchestrator

logger = logging.getLogger(__name__)

REJECT_REASONS = {
    "promo": "Too promotional",
    "voice": "Wrong voice/tone",
    "topic": "Not relevant to niche",
    "quality": "Low quality",
    "other": "Other (type your reason)",
}


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks for Approve/Edit/Reject/Later/Feedback."""
    query = update.callback_query
    authorized = get_authorized_chat_id()
    if authorized and query.message.chat.id != authorized:
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.answer()

    data = query.data
    parts = data.split(":")

    if len(parts) < 2:
        await query.edit_message_text("Invalid callback data.")
        return

    action = parts[0]
    thread_id = parts[1]

    # --- Approve ---
    if action == "approve":
        decision = {"decision": "approve"}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- APPROVED ---",
        )
        await _resume_graph(thread_id, decision)

    # --- Reject → show reason buttons ---
    elif action == "reject":
        keyboard = []
        for code, label in REJECT_REASONS.items():
            keyboard.append([InlineKeyboardButton(label, callback_data=f"rjfb:{thread_id}:{code}")])
        await query.edit_message_text(
            f"{query.message.text}\n\n--- Why reject? ---",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Reject feedback selection ---
    elif action == "rjfb":
        reason_code = parts[2] if len(parts) > 2 else "other"
        if reason_code == "other":
            context.user_data["awaiting_reject_feedback"] = thread_id
            await query.edit_message_text(
                f"{query.message.text}\n\nType your rejection reason:",
            )
            return

        feedback = REJECT_REASONS.get(reason_code, reason_code)
        decision = {"decision": "reject", "feedback": feedback}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- REJECTED: {feedback} ---",
        )
        await _resume_graph(thread_id, decision)

    # --- Edit ---
    elif action == "edit":
        await query.edit_message_text(
            f"{query.message.text}\n\n--- EDIT MODE ---\n"
            "Please send the edited post text as a reply.",
        )
        context.user_data["awaiting_edit"] = thread_id

    # --- Use alternative ---
    elif action == "alt":
        alt_index = int(parts[2]) if len(parts) > 2 else 0
        decision = {"decision": "approve", "use_alternative": alt_index}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- APPROVED (Alt {alt_index + 1}) ---",
        )
        await _resume_graph(thread_id, decision)

    # --- Publish Later → show time options ---
    elif action == "later":
        keyboard = [
            [
                InlineKeyboardButton("In 1h", callback_data=f"pub_at:{thread_id}:1h"),
                InlineKeyboardButton("In 3h", callback_data=f"pub_at:{thread_id}:3h"),
            ],
            [
                InlineKeyboardButton("Tomorrow 8:00", callback_data=f"pub_at:{thread_id}:t08"),
                InlineKeyboardButton("Tomorrow 12:00", callback_data=f"pub_at:{thread_id}:t12"),
            ],
            [
                InlineKeyboardButton("Tomorrow 18:00", callback_data=f"pub_at:{thread_id}:t18"),
            ],
        ]
        await query.edit_message_text(
            f"{query.message.text}\n\n--- When to publish? ---",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Publish at selected time ---
    elif action == "pub_at":
        time_code = parts[2] if len(parts) > 2 else "1h"
        publish_at = _resolve_publish_time(time_code)
        decision = {"decision": "approve", "publish_at": publish_at.isoformat()}
        await query.edit_message_text(
            f"{query.message.text}\n\n--- SCHEDULED: {publish_at.strftime('%Y-%m-%d %H:%M')} UTC ---",
        )
        await _resume_graph(thread_id, decision)

    else:
        await query.edit_message_text("Unknown action.")


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


async def handle_reject_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle typed rejection feedback after selecting 'Other'."""
    thread_id = context.user_data.get("awaiting_reject_feedback")
    if not thread_id:
        return

    feedback = update.message.text.strip()
    del context.user_data["awaiting_reject_feedback"]

    await update.message.reply_text(f"Rejection feedback received: {feedback}")

    decision = {"decision": "reject", "feedback": feedback}
    await _resume_graph(thread_id, decision)


def _resolve_publish_time(code: str) -> datetime:
    """Convert a time code to a UTC datetime."""
    now = datetime.now(timezone.utc)

    if code == "1h":
        return now + timedelta(hours=1)
    elif code == "3h":
        return now + timedelta(hours=3)
    elif code.startswith("t"):
        hour = int(code[1:])
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)

    return now + timedelta(hours=1)


async def _resume_graph(thread_id: str, decision: dict) -> None:
    """Resume the paused graph with the human's decision via the orchestrator."""
    orchestrator = get_orchestrator()
    if orchestrator is None:
        logger.error("Orchestrator not set — cannot resume graph")
        return

    try:
        await orchestrator.resume_creation(thread_id, decision)
        logger.info(f"Graph resumed for thread_id={thread_id} with decision={decision}")
    except Exception as e:
        logger.error(f"Failed to resume graph for thread_id={thread_id}: {e}")
