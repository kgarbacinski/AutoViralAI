import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.dependencies import get_authorized_chat_id, get_knowledge_base, get_orchestrator

logger = logging.getLogger(__name__)

TONE_OPTIONS = [
    "conversational",
    "professional",
    "provocative",
    "educational",
    "humorous",
]

LANGUAGE_OPTIONS = [
    "English",
    "Polish",
    "Spanish",
    "German",
]


async def handle_config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    authorized = get_authorized_chat_id()
    if not authorized or query.message.chat.id != authorized:
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.answer()

    data = query.data
    parts = data.split(":")

    if len(parts) < 2:
        return

    setting = parts[1]
    value = parts[2] if len(parts) > 2 else None

    if value is None:
        if setting == "tone":
            keyboard = [
                [InlineKeyboardButton(t, callback_data=f"cfg:tone:{t}")] for t in TONE_OPTIONS
            ]
            await query.edit_message_text(
                "Select tone:", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "language":
            keyboard = [
                [InlineKeyboardButton(lang, callback_data=f"cfg:language:{lang}")]
                for lang in LANGUAGE_OPTIONS
            ]
            await query.edit_message_text(
                "Select language:", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "hashtags":
            keyboard = [
                [InlineKeyboardButton(str(n), callback_data=f"cfg:hashtags:{n}")]
                for n in [1, 2, 3, 4, 5]
            ]
            await query.edit_message_text(
                "Max hashtags per post:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif setting == "max_posts":
            keyboard = [
                [InlineKeyboardButton(str(n), callback_data=f"cfg:max_posts:{n}")]
                for n in [1, 2, 3, 4, 5]
            ]
            await query.edit_message_text(
                "Max posts per day:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif setting == "avoid":
            keyboard = [
                [InlineKeyboardButton("Add topic", callback_data="cfg:avoid:add")],
                [InlineKeyboardButton("Clear all", callback_data="cfg:avoid:clear")],
            ]
            await query.edit_message_text(
                "Avoid topics:", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "schedule":
            keyboard = [
                [InlineKeyboardButton(f"{h}:00", callback_data=f"cfg:schedule:{h}")]
                for h in [6, 8, 9, 10, 12, 14, 16, 18, 20]
            ]
            await query.edit_message_text(
                "Select posting hours (pick one at a time, re-open /config to add more).\n"
                "Current schedule will be replaced.",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return

    kb = get_knowledge_base()
    if not kb:
        await query.edit_message_text("Knowledge base not available.")
        return

    try:
        niche = await kb.get_niche_config()
        if not niche:
            await query.edit_message_text("No config found.")
            return

        if setting == "tone":
            niche.voice.tone = value
            await kb.save_niche_config(niche)
            await query.edit_message_text(f"Tone updated to: {value}")

        elif setting == "language":
            niche.voice.language = value
            await kb.save_niche_config(niche)
            await query.edit_message_text(f"Language updated to: {value}")

        elif setting == "hashtags":
            try:
                niche.max_hashtags_per_post = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text("Invalid value for max hashtags.")
                return
            await kb.save_niche_config(niche)
            await query.edit_message_text(f"Max hashtags updated to: {value}")

        elif setting == "max_posts":
            try:
                niche.max_posts_per_day = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text("Invalid value for max posts.")
                return
            await kb.save_niche_config(niche)
            await query.edit_message_text(f"Max posts/day updated to: {value}")

        elif setting == "avoid":
            if value == "clear":
                niche.avoid_topics = []
                await kb.save_niche_config(niche)
                await query.edit_message_text("Avoid topics cleared.")
            elif value == "add":
                context.user_data["awaiting_config_input"] = "avoid_topic"
                await query.edit_message_text("Type the topic to avoid:")

        elif setting == "schedule":
            try:
                hour = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text("Invalid schedule value.")
                return
            orchestrator = get_orchestrator()
            if not orchestrator:
                await query.edit_message_text("Orchestrator not available.")
                return

            time_str = f"{hour:02d}:00"
            if time_str not in niche.preferred_posting_times:
                niche.preferred_posting_times.append(time_str)
                niche.preferred_posting_times.sort()
                await kb.save_niche_config(niche)

            orchestrator.reschedule_creation_jobs(niche.preferred_posting_times)
            await query.edit_message_text(
                f"Schedule updated. Posting times: {', '.join(niche.preferred_posting_times)}\n"
                "Jobs have been rescheduled."
            )

    except Exception:
        logger.exception("Config update failed")
        await query.edit_message_text("Failed to update config. Check server logs for details.")


async def handle_config_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    authorized = get_authorized_chat_id()
    if not authorized or update.message.chat.id != authorized:
        return

    input_type = context.user_data.get("awaiting_config_input")
    if not input_type:
        return

    text = update.message.text.strip()

    if len(text) > 200:
        await update.message.reply_text("Input too long (max 200 characters). Try again.")
        return

    del context.user_data["awaiting_config_input"]

    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    if input_type == "avoid_topic":
        try:
            niche = await kb.get_niche_config()
            if niche:
                niche.avoid_topics.append(text)
                await kb.save_niche_config(niche)
                await update.message.reply_text(
                    f"Added '{text}' to avoid topics.\nCurrent: {', '.join(niche.avoid_topics)}"
                )
        except Exception:
            logger.exception("Failed to add avoid topic")
            await update.message.reply_text("Failed to add topic. Check server logs for details.")
