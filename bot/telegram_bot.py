"""Telegram bot setup for human-in-the-loop approval."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.handlers.approval import handle_approval_callback, handle_edit_message
from bot.handlers.status import handle_status_command

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "Threads Agent Bot active.\n\n"
        "Commands:\n"
        "/status - Check agent status\n\n"
        "I'll send you posts for approval when they're ready."
    )


def create_bot(token: str) -> Application:
    """Create and configure the Telegram bot application."""
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", handle_status_command))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_message))

    return app


async def send_approval_request(
    app: Application,
    chat_id: str,
    thread_id: str,
    selected_post: dict,
    alternatives: list[dict],
    cycle_number: int,
    follower_count: int,
) -> None:
    """Send a post approval request to the user via Telegram."""
    content = selected_post.get("content", "")
    score = selected_post.get("composite_score", 0)
    pattern = selected_post.get("pattern_used", "unknown")

    message = (
        f"**New Post for Approval** (Cycle #{cycle_number})\n"
        f"Followers: {follower_count}\n\n"
        f"---\n"
        f"{content}\n"
        f"---\n\n"
        f"Pattern: {pattern} | Score: {score:.1f}/10\n"
    )

    if alternatives:
        message += "\n**Alternatives:**\n"
        for i, alt in enumerate(alternatives, 1):
            message += (
                f"\n{i}. [{alt.get('pattern_used', '?')} | "
                f"{alt.get('composite_score', 0):.1f}]\n"
                f"{alt.get('content', '')[:150]}...\n"
            )

    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{thread_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{thread_id}"),
        ],
        [
            InlineKeyboardButton("Edit", callback_data=f"edit:{thread_id}"),
        ],
    ]

    for i, alt in enumerate(alternatives):
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Use Alt {i + 1}",
                    callback_data=f"alt:{thread_id}:{i}",
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await app.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
