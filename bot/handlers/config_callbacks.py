import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.dependencies import get_authorized_chat_id, get_knowledge_base, get_orchestrator
from bot.messages import (
    CONFIG_ADD_TOPIC_FAILED,
    CONFIG_AVOID_CLEARED,
    CONFIG_AVOID_TOPIC_ADDED,
    CONFIG_AVOID_TOPICS,
    CONFIG_HASHTAGS_UPDATED,
    CONFIG_INPUT_TOO_LONG,
    CONFIG_INVALID_HASHTAGS,
    CONFIG_INVALID_MAX_POSTS,
    CONFIG_INVALID_SCHEDULE,
    CONFIG_LANGUAGE_UPDATED,
    CONFIG_MAX_HASHTAGS,
    CONFIG_MAX_POSTS_PER_DAY,
    CONFIG_MAX_POSTS_UPDATED,
    CONFIG_NO_CONFIG,
    CONFIG_SCHEDULE_UPDATED,
    CONFIG_SELECT_LANGUAGE,
    CONFIG_SELECT_SCHEDULE,
    CONFIG_SELECT_TONE,
    CONFIG_TONE_UPDATED,
    CONFIG_TYPE_AVOID_TOPIC,
    CONFIG_UPDATE_FAILED,
    KB_NOT_AVAILABLE,
    ORCHESTRATOR_NOT_AVAILABLE,
    UNAUTHORIZED,
)
from src.exceptions import KnowledgeBaseError

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
        await query.answer(UNAUTHORIZED, show_alert=True)
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
                CONFIG_SELECT_TONE, reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "language":
            keyboard = [
                [InlineKeyboardButton(lang, callback_data=f"cfg:language:{lang}")]
                for lang in LANGUAGE_OPTIONS
            ]
            await query.edit_message_text(
                CONFIG_SELECT_LANGUAGE, reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "hashtags":
            keyboard = [
                [InlineKeyboardButton(str(n), callback_data=f"cfg:hashtags:{n}")]
                for n in [1, 2, 3, 4, 5]
            ]
            await query.edit_message_text(
                CONFIG_MAX_HASHTAGS,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif setting == "max_posts":
            keyboard = [
                [InlineKeyboardButton(str(n), callback_data=f"cfg:max_posts:{n}")]
                for n in [1, 2, 3, 4, 5]
            ]
            await query.edit_message_text(
                CONFIG_MAX_POSTS_PER_DAY,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif setting == "avoid":
            keyboard = [
                [InlineKeyboardButton("Add topic", callback_data="cfg:avoid:add")],
                [InlineKeyboardButton("Clear all", callback_data="cfg:avoid:clear")],
            ]
            await query.edit_message_text(
                CONFIG_AVOID_TOPICS, reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif setting == "schedule":
            keyboard = [
                [InlineKeyboardButton(f"{h}:00", callback_data=f"cfg:schedule:{h}")]
                for h in [6, 8, 9, 10, 12, 14, 16, 18, 20]
            ]
            await query.edit_message_text(
                CONFIG_SELECT_SCHEDULE,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return

    kb = get_knowledge_base()
    if not kb:
        await query.edit_message_text(KB_NOT_AVAILABLE)
        return

    try:
        niche = await kb.get_niche_config()
        if not niche:
            await query.edit_message_text(CONFIG_NO_CONFIG)
            return

        if setting == "tone":
            niche.voice.tone = value
            await kb.save_niche_config(niche)
            await query.edit_message_text(CONFIG_TONE_UPDATED.format(value=value))

        elif setting == "language":
            niche.voice.language = value
            await kb.save_niche_config(niche)
            await query.edit_message_text(CONFIG_LANGUAGE_UPDATED.format(value=value))

        elif setting == "hashtags":
            try:
                niche.max_hashtags_per_post = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text(CONFIG_INVALID_HASHTAGS)
                return
            await kb.save_niche_config(niche)
            await query.edit_message_text(CONFIG_HASHTAGS_UPDATED.format(value=value))

        elif setting == "max_posts":
            try:
                niche.max_posts_per_day = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text(CONFIG_INVALID_MAX_POSTS)
                return
            await kb.save_niche_config(niche)
            await query.edit_message_text(CONFIG_MAX_POSTS_UPDATED.format(value=value))

        elif setting == "avoid":
            if value == "clear":
                niche.avoid_topics = []
                await kb.save_niche_config(niche)
                await query.edit_message_text(CONFIG_AVOID_CLEARED)
            elif value == "add":
                context.user_data["awaiting_config_input"] = "avoid_topic"
                await query.edit_message_text(CONFIG_TYPE_AVOID_TOPIC)

        elif setting == "schedule":
            try:
                hour = int(value)
            except (ValueError, TypeError):
                await query.edit_message_text(CONFIG_INVALID_SCHEDULE)
                return
            orchestrator = get_orchestrator()
            if not orchestrator:
                await query.edit_message_text(ORCHESTRATOR_NOT_AVAILABLE)
                return

            time_str = f"{hour:02d}:00"
            if time_str not in niche.preferred_posting_times:
                niche.preferred_posting_times.append(time_str)
                niche.preferred_posting_times.sort()
                await kb.save_niche_config(niche)

            orchestrator.reschedule_creation_jobs(niche.preferred_posting_times)
            await query.edit_message_text(
                CONFIG_SCHEDULE_UPDATED.format(times=", ".join(niche.preferred_posting_times))
            )

    except KnowledgeBaseError:
        logger.exception("Config update failed")
        await query.edit_message_text(CONFIG_UPDATE_FAILED)


async def handle_config_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    authorized = get_authorized_chat_id()
    if not authorized or update.message.chat.id != authorized:
        return

    input_type = context.user_data.get("awaiting_config_input")
    if not input_type:
        return

    text = update.message.text.strip()

    if len(text) > 200:
        await update.message.reply_text(CONFIG_INPUT_TOO_LONG)
        return

    del context.user_data["awaiting_config_input"]

    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text(KB_NOT_AVAILABLE)
        return

    if input_type == "avoid_topic":
        try:
            niche = await kb.get_niche_config()
            if niche:
                niche.avoid_topics.append(text)
                await kb.save_niche_config(niche)
                await update.message.reply_text(
                    CONFIG_AVOID_TOPIC_ADDED.format(
                        topic=text, current=", ".join(niche.avoid_topics)
                    )
                )
        except KnowledgeBaseError:
            logger.exception("Failed to add avoid topic")
            await update.message.reply_text(CONFIG_ADD_TOPIC_FAILED)
