import logging
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.handlers.approval import (
    handle_approval_callback,
    handle_edit_message,
    handle_reject_feedback_text,
)
from bot.handlers.commands import (
    handle_config_command,
    handle_force_command,
    handle_history_command,
    handle_learn_command,
    handle_metrics_command,
    handle_pause_command,
    handle_research_command,
    handle_resume_command,
    handle_schedule_command,
)
from bot.handlers.config_callbacks import handle_config_callback, handle_config_text_input
from bot.handlers.status import handle_status_command
from bot.messages import (
    APPROVAL_ALTERNATIVE_MSG,
    APPROVAL_ALTERNATIVES_HEADER,
    APPROVAL_BEST_TIME,
    APPROVAL_PATTERN,
    APPROVAL_PATTERN_WITH_RATIONALE,
    APPROVAL_RECENT_POSTS_HEADER,
    APPROVAL_REQUEST_HEADER,
    APPROVAL_SCORE,
    APPROVAL_SCORE_WITH_AVG,
    CREATION_PIPELINE_FAILED_NOTIFY,
    ENRICHMENT_NEW_PATTERN,
    ENRICHMENT_PATTERN_RATIONALE,
    HELP_TEXT,
    REPORT_GENERATION_HEADER,
    REPORT_PATTERNS_HEADER,
    REPORT_RANKING_HEADER,
    REPORT_RESEARCH_HEADER,
    REPORT_RESEARCH_SOURCES,
    REPORT_TOP_BY_ENGAGEMENT,
    START_MESSAGE,
)
from src.exceptions import KnowledgeBaseError

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


def create_bot(token: str, authorized_chat_id: str = "") -> Application:
    app = Application.builder().token(token).build()

    if not authorized_chat_id:
        logger.warning(
            "No TELEGRAM_CHAT_ID set — only /start and /help available. "
            "Set TELEGRAM_CHAT_ID to enable all commands."
        )
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        return app

    chat_filter = filters.Chat(chat_id=int(authorized_chat_id))
    text_filter = filters.TEXT & ~filters.COMMAND & chat_filter

    app.add_handler(CommandHandler("start", start_command, filters=chat_filter))
    app.add_handler(CommandHandler("help", help_command, filters=chat_filter))
    app.add_handler(CommandHandler("status", handle_status_command, filters=chat_filter))
    app.add_handler(CommandHandler("metrics", handle_metrics_command, filters=chat_filter))
    app.add_handler(CommandHandler("history", handle_history_command, filters=chat_filter))
    app.add_handler(CommandHandler("schedule", handle_schedule_command, filters=chat_filter))
    app.add_handler(CommandHandler("force", handle_force_command, filters=chat_filter))
    app.add_handler(CommandHandler("learn", handle_learn_command, filters=chat_filter))
    app.add_handler(CommandHandler("research", handle_research_command, filters=chat_filter))
    app.add_handler(CommandHandler("pause", handle_pause_command, filters=chat_filter))
    app.add_handler(CommandHandler("resume", handle_resume_command, filters=chat_filter))
    app.add_handler(CommandHandler("config", handle_config_command, filters=chat_filter))

    app.add_handler(CallbackQueryHandler(handle_config_callback, pattern=r"^cfg:"))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))

    app.add_handler(MessageHandler(text_filter, _handle_text_message))

    return app


async def _handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("awaiting_reject_feedback"):
        await handle_reject_feedback_text(update, context)
    elif context.user_data.get("awaiting_edit"):
        await handle_edit_message(update, context)
    elif context.user_data.get("awaiting_config_input"):
        await handle_config_text_input(update, context)


async def send_pipeline_report(app: Application, chat_id: str, state_values: dict) -> None:
    sections = []

    viral_posts = state_values.get("viral_posts", [])
    if viral_posts:
        sections.append(_build_research_section(viral_posts))

    patterns = state_values.get("extracted_patterns", [])
    if patterns:
        sections.append(_build_patterns_section(patterns))

    variants = state_values.get("generated_variants", [])
    if variants:
        sections.append(_build_generation_section(variants))

    ranked = state_values.get("ranked_posts", [])
    if ranked:
        sections.append(_build_ranking_section(ranked))

    if not sections:
        return

    messages = _split_report_messages(sections)

    for msg in messages:
        try:
            await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
        except TelegramError as e:
            logger.error("Failed to send pipeline report section: %s", e)


def _build_research_section(viral_posts: list[dict]) -> str:
    hn_count = sum(1 for p in viral_posts if p.get("platform") == "hackernews")
    threads_count = sum(1 for p in viral_posts if p.get("platform") == "threads")

    lines = [REPORT_RESEARCH_HEADER.format(count=len(viral_posts))]
    lines.append(REPORT_RESEARCH_SOURCES.format(hn=hn_count, threads=threads_count))

    sorted_posts = sorted(viral_posts, key=lambda p: p.get("engagement_rate", 0), reverse=True)
    lines.append(REPORT_TOP_BY_ENGAGEMENT)
    for i, post in enumerate(sorted_posts[:3], 1):
        content = escape(post.get("content", "")[:80])
        er = post.get("engagement_rate", 0)
        likes = post.get("likes", 0)
        lines.append(f'  {i}. "{content}..." — {er:.1%} ER, {likes} likes')

    return "\n".join(lines)


def _build_patterns_section(patterns: list[dict]) -> str:
    lines = [REPORT_PATTERNS_HEADER.format(count=len(patterns))]

    for i, pat in enumerate(patterns[:5], 1):
        name = escape(pat.get("name", "?"))
        hook = escape(pat.get("hook_type", "?"))
        desc = escape(pat.get("description", "")[:100])
        structure = escape(pat.get("structure", "?"))
        src_count = pat.get("source_posts_count", 0)
        lines.append(f"  {i}. <b>{name}</b> ({hook} hook)")
        lines.append(f'     "{desc}"')
        lines.append(f"     Structure: {structure}")
        lines.append(f"     Found in {src_count} viral posts")
        lines.append("")

    return "\n".join(lines)


def _build_generation_section(variants: list[dict]) -> str:
    lines = [REPORT_GENERATION_HEADER.format(count=len(variants))]

    for i, var in enumerate(variants[:5], 1):
        pattern = escape(var.get("pattern_used", "?"))
        pillar = escape(var.get("pillar", "?"))
        est = var.get("estimated_engagement", "unknown")
        content = escape(var.get("content", "")[:100])
        lines.append(f"  {i}. [{pattern}] [{pillar}] est: {est}")
        lines.append(f'     "{content}..."')

    return "\n".join(lines)


def _build_ranking_section(ranked: list[dict]) -> str:
    lines = [REPORT_RANKING_HEADER]

    for i, post in enumerate(ranked[:5], 1):
        composite = post.get("composite_score", 0)
        ai = post.get("ai_score", 0)
        hist = post.get("pattern_history_score", 0)
        novelty = post.get("novelty_score", 0)
        pattern = escape(post.get("pattern_used", "?"))
        pillar = escape(post.get("pillar", "?"))
        reasoning = escape(post.get("reasoning", "")[:100])
        star = " ⭐" if i == 1 else ""
        lines.append(f"  #{i}{star} {composite:.1f}/10  [AI:{ai:.1f} H:{hist:.1f} N:{novelty:.1f}]")
        lines.append(f"     Pattern: {pattern} | Pillar: {pillar}")
        if reasoning:
            lines.append(f'     "{reasoning}"')
        lines.append("")

    return "\n".join(lines)


def _split_report_messages(sections: list[str]) -> list[str]:
    messages = []
    current = ""

    for section in sections:
        candidate = f"{current}\n\n{section}" if current else section
        if len(candidate) > TELEGRAM_MAX_MESSAGE_LENGTH:
            if current:
                messages.append(current)
            if len(section) > TELEGRAM_MAX_MESSAGE_LENGTH:
                messages.append(section[: TELEGRAM_MAX_MESSAGE_LENGTH - 3] + "...")
            else:
                current = section
                continue
        else:
            current = candidate
            continue
        current = ""

    if current:
        messages.append(current)

    return messages


async def build_enrichment_data(kb, selected_post: dict) -> dict:
    enrichment = {}

    try:
        metrics_history = await kb.get_metrics_history(limit=5)
        if metrics_history:
            recent_metrics = []
            for m in metrics_history[:5]:
                recent_metrics.append(
                    {
                        "content_preview": m.content[:50] if m.content else "?",
                        "engagement_rate": m.engagement_rate,
                        "likes": m.likes,
                        "replies": m.replies,
                    }
                )
            enrichment["recent_metrics"] = recent_metrics

            ers = [m.engagement_rate for m in metrics_history]
            enrichment["avg_engagement_rate"] = sum(ers) / len(ers) if ers else 0
    except KnowledgeBaseError as e:
        logger.warning("Failed to fetch recent metrics for enrichment: %s", e)

    try:
        pattern_name = selected_post.get("pattern_used", "")
        if pattern_name:
            perf = await kb.get_pattern_performance(pattern_name)
            enrichment["pattern_rationale"] = (
                ENRICHMENT_PATTERN_RATIONALE.format(
                    avg_er=perf.avg_engagement_rate, times_used=perf.times_used
                )
                if perf.times_used > 0
                else ENRICHMENT_NEW_PATTERN
            )
    except KnowledgeBaseError as e:
        logger.warning("Failed to fetch pattern performance for enrichment: %s", e)

    try:
        strategy = await kb.get_strategy()
        if strategy.optimal_posting_times:
            enrichment["optimal_time"] = ", ".join(strategy.optimal_posting_times[:3])
    except KnowledgeBaseError as e:
        logger.warning("Failed to fetch strategy for enrichment: %s", e)

    try:
        recent_posts = await kb.get_recent_posts(limit=10)
        if recent_posts:
            avg_score = sum(p.composite_score for p in recent_posts) / len(recent_posts)
            enrichment["avg_score"] = avg_score
    except KnowledgeBaseError as e:
        logger.warning("Failed to fetch recent posts for benchmark: %s", e)

    return enrichment


async def send_approval_request(
    app: Application,
    chat_id: str,
    thread_id: str,
    selected_post: dict,
    alternatives: list[dict],
    cycle_number: int,
    follower_count: int,
    enrichment: dict | None = None,
) -> None:
    content = escape(selected_post.get("content", ""))
    score = selected_post.get("composite_score", 0)
    pattern = escape(selected_post.get("pattern_used", "unknown"))

    message = APPROVAL_REQUEST_HEADER.format(
        cycle=cycle_number, followers=follower_count, content=content
    )

    if enrichment and "avg_score" in enrichment:
        avg = enrichment["avg_score"]
        diff = score - avg
        sign = "+" if diff >= 0 else ""
        message += APPROVAL_SCORE_WITH_AVG.format(score=score, sign=sign, diff=diff, avg=avg)
    else:
        message += APPROVAL_SCORE.format(score=score)

    if enrichment and "pattern_rationale" in enrichment:
        rationale = escape(enrichment["pattern_rationale"])
        message += APPROVAL_PATTERN_WITH_RATIONALE.format(pattern=pattern, rationale=rationale)
    else:
        message += APPROVAL_PATTERN.format(pattern=pattern)

    if enrichment and "optimal_time" in enrichment:
        message += APPROVAL_BEST_TIME.format(time=escape(enrichment["optimal_time"]))

    if enrichment and "recent_metrics" in enrichment:
        message += APPROVAL_RECENT_POSTS_HEADER
        for i, m in enumerate(enrichment["recent_metrics"][:3], 1):
            er = m["engagement_rate"]
            likes = m["likes"]
            replies = m["replies"]
            preview = escape(m["content_preview"])
            message += f'  {i}. {er:.2%} ER | {likes}L {replies}R | "{preview}..."\n'

    if alternatives:
        message += APPROVAL_ALTERNATIVES_HEADER
        for i, alt in enumerate(alternatives, 1):
            alt_pattern = escape(alt.get("pattern_used", "?"))
            message += f"  {i}. [{alt_pattern} | {alt.get('composite_score', 0):.1f}]\n"

    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{thread_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{thread_id}"),
        ],
        [
            InlineKeyboardButton("Edit", callback_data=f"edit:{thread_id}"),
            InlineKeyboardButton("Publish Later", callback_data=f"later:{thread_id}"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await app.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

    for i, alt in enumerate(alternatives):
        alt_content = escape(alt.get("content", ""))
        alt_pattern = escape(alt.get("pattern_used", "?"))
        alt_score = alt.get("composite_score", 0)
        alt_message = APPROVAL_ALTERNATIVE_MSG.format(
            index=i + 1,
            cycle=cycle_number,
            pattern=alt_pattern,
            score=alt_score,
            content=alt_content,
        )
        alt_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"Use Alt {i + 1}",
                        callback_data=f"alt:{thread_id}:{i}",
                    )
                ]
            ]
        )
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=alt_message,
                reply_markup=alt_keyboard,
                parse_mode="HTML",
            )
        except TelegramError as e:
            logger.error("Failed to send alternative %d: %s", i + 1, e)


async def send_creation_failure(
    app: Application,
    chat_id: str,
    cycle_number: int,
    errors: list[str],
    next_run_time: str = "",
) -> None:
    limited_errors = errors[:5]
    if limited_errors:
        error_text = "\n".join(f"• {escape(str(e))}" for e in limited_errors)
    else:
        error_text = "• No error details captured"
    if len(errors) > 5:
        error_text += f"\n... and {len(errors) - 5} more"

    message = CREATION_PIPELINE_FAILED_NOTIFY.format(
        cycle=cycle_number,
        errors=error_text,
        next_run=escape(next_run_time) if next_run_time else "check /schedule",
    )

    try:
        await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except TelegramError as e:
        logger.error("Failed to send creation failure notification: %s", e)
