"""Status command handler for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes


async def handle_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show agent status."""
    status_text = (
        "**AutoViralAI Status**\n\n"
        "Status: Running\n"
        "Environment: Development\n"
        "Pipeline: Idle\n\n"
        "Use the web dashboard for detailed metrics."
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")
