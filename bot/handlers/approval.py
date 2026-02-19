import logging
from datetime import UTC, datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.dependencies import get_authorized_chat_id, get_orchestrator
from bot.messages import (
    APPROVED_ALT_SUFFIX,
    APPROVED_SUFFIX,
    EDIT_MODE_SUFFIX,
    EDIT_RECEIVED,
    FEEDBACK_TOO_LONG,
    INVALID_CALLBACK,
    POST_TOO_LONG,
    REJECT_PROMPT_SUFFIX,
    REJECT_TYPE_REASON,
    REJECTED_SUFFIX,
    REJECTION_FEEDBACK_RECEIVED,
    SCHEDULE_PROMPT_SUFFIX,
    SCHEDULED_SUFFIX,
    UNAUTHORIZED,
    UNKNOWN_ACTION,
)

logger = logging.getLogger(__name__)

MAX_POST_LENGTH = 500

REJECT_REASONS = {
    "promo": "Too promotional",
    "voice": "Wrong voice/tone",
    "topic": "Not relevant to niche",
    "quality": "Low quality",
    "other": "Other (type your reason)",
}


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    authorized = get_authorized_chat_id()
    if not authorized or query.message.chat.id != authorized:
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    await query.answer()

    data = query.data
    parts = data.split(":")

    if len(parts) < 2:
        await query.edit_message_text(INVALID_CALLBACK)
        return

    action = parts[0]
    thread_id = parts[1]

    if action == "approve":
        decision = {"decision": "approve"}
        await query.edit_message_text(
            f"{query.message.text}{APPROVED_SUFFIX}",
        )
        await _resume_graph(thread_id, decision)

    elif action == "reject":
        keyboard = []
        for code, label in REJECT_REASONS.items():
            keyboard.append([InlineKeyboardButton(label, callback_data=f"rjfb:{thread_id}:{code}")])
        await query.edit_message_text(
            f"{query.message.text}{REJECT_PROMPT_SUFFIX}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "rjfb":
        reason_code = parts[2] if len(parts) > 2 else "other"
        if reason_code == "other":
            context.user_data["awaiting_reject_feedback"] = thread_id
            await query.edit_message_text(
                f"{query.message.text}\n\n{REJECT_TYPE_REASON}",
            )
            return

        feedback = REJECT_REASONS.get(reason_code, reason_code)
        decision = {"decision": "reject", "feedback": feedback}
        await query.edit_message_text(
            f"{query.message.text}{REJECTED_SUFFIX.format(feedback=feedback)}",
        )
        await _resume_graph(thread_id, decision)

    elif action == "edit":
        await query.edit_message_text(
            f"{query.message.text}{EDIT_MODE_SUFFIX}",
        )
        context.user_data["awaiting_edit"] = thread_id

    elif action == "alt":
        try:
            alt_index = int(parts[2]) if len(parts) > 2 else 0
        except (ValueError, IndexError):
            alt_index = 0
        decision = {"decision": "approve", "use_alternative": alt_index}
        await query.edit_message_text(
            f"{query.message.text}{APPROVED_ALT_SUFFIX.format(index=alt_index + 1)}",
        )
        await _resume_graph(thread_id, decision)

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
            f"{query.message.text}{SCHEDULE_PROMPT_SUFFIX}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "pub_at":
        time_code = parts[2] if len(parts) > 2 else "1h"
        publish_at = _resolve_publish_time(time_code)
        decision = {"decision": "approve", "publish_at": publish_at.isoformat()}
        scheduled_str = publish_at.strftime("%Y-%m-%d %H:%M")
        await query.edit_message_text(
            f"{query.message.text}{SCHEDULED_SUFFIX.format(time=scheduled_str)}",
        )
        await _resume_graph(thread_id, decision)

    else:
        await query.edit_message_text(UNKNOWN_ACTION)


async def handle_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    authorized = get_authorized_chat_id()
    if not authorized or update.message.chat.id != authorized:
        return

    thread_id = context.user_data.get("awaiting_edit")
    if not thread_id:
        return

    edited_content = update.message.text.strip()
    del context.user_data["awaiting_edit"]

    if len(edited_content) > MAX_POST_LENGTH:
        await update.message.reply_text(POST_TOO_LONG.format(max_length=MAX_POST_LENGTH))
        context.user_data["awaiting_edit"] = thread_id
        return

    await update.message.reply_text(EDIT_RECEIVED)

    decision = {"decision": "edit", "edited_content": edited_content}
    await _resume_graph(thread_id, decision)


async def handle_reject_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    authorized = get_authorized_chat_id()
    if not authorized or update.message.chat.id != authorized:
        return

    thread_id = context.user_data.get("awaiting_reject_feedback")
    if not thread_id:
        return

    feedback = update.message.text.strip()

    if len(feedback) > MAX_POST_LENGTH:
        await update.message.reply_text(FEEDBACK_TOO_LONG.format(max_length=MAX_POST_LENGTH))
        return

    del context.user_data["awaiting_reject_feedback"]

    await update.message.reply_text(REJECTION_FEEDBACK_RECEIVED.format(feedback=feedback))

    decision = {"decision": "reject", "feedback": feedback}
    await _resume_graph(thread_id, decision)


def _resolve_publish_time(code: str) -> datetime:
    now = datetime.now(UTC)

    if code == "1h":
        return now + timedelta(hours=1)
    elif code == "3h":
        return now + timedelta(hours=3)
    elif code.startswith("t"):
        try:
            hour = int(code[1:])
        except ValueError:
            return now + timedelta(hours=1)
        if not (0 <= hour <= 23):
            return now + timedelta(hours=1)
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)

    return now + timedelta(hours=1)


async def _resume_graph(thread_id: str, decision: dict) -> None:
    orchestrator = get_orchestrator()
    if orchestrator is None:
        logger.error("Orchestrator not set — cannot resume graph")
        return

    try:
        await orchestrator.resume_creation(thread_id, decision)
        logger.info("Graph resumed for thread_id=%s with decision=%s", thread_id, decision)
    except Exception:
        logger.exception("Failed to resume graph for thread_id=%s", thread_id)
