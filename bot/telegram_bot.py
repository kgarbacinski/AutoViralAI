import logging
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from bot.handlers.status import handle_status_command

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


HELP_TEXT = (
    "🤖 <b>AutoViralAI — Command Reference</b>\n\n"
    "📊 <b>Monitoring</b>\n"
    "/status — Live agent status (running/paused, cycles, pending approvals, next run)\n"
    "/metrics — Performance metrics: avg ER, trend, top patterns, key learnings\n"
    "/history — Last 10 published posts with scores and engagement data\n"
    "/schedule — Scheduled jobs and AI-recommended posting times\n\n"
    "⚙️ <b>Pipeline Control</b>\n"
    "/force — Trigger creation pipeline now (blocked if approvals pending)\n"
    "/learn — Trigger learning pipeline (collect metrics, analyze, update strategy)\n"
    "/research — Run standalone viral research without the full pipeline\n"
    "/pause — Pause all scheduled pipelines\n"
    "/resume — Resume paused pipelines\n\n"
    "🔧 <b>Configuration</b>\n"
    "/config — View and edit: tone, language, hashtags, schedule, avoid topics\n\n"
    "📎 <b>Other</b>\n"
    "/start — Welcome message\n"
    "/help — This command reference\n\n"
    "<i>When a post is ready, I'll send a pipeline report + approval message with buttons.</i>"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "AutoViralAI Bot active.\n\n"
        "Type /help to see all available commands.\n\n"
        "I'll send you posts for approval when they're ready."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


def create_bot(token: str, authorized_chat_id: str = "") -> Application:
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
    from bot.handlers.config_callbacks import handle_config_callback

    app = Application.builder().token(token).build()

    chat_filter = filters.Chat(chat_id=int(authorized_chat_id)) if authorized_chat_id else None

    if chat_filter:
        cmd_filter = chat_filter
        text_filter = filters.TEXT & ~filters.COMMAND & chat_filter
    else:
        logger.warning("No TELEGRAM_CHAT_ID set — bot commands are unrestricted!")
        cmd_filter = None
        text_filter = filters.TEXT & ~filters.COMMAND

    app.add_handler(CommandHandler("start", start_command, filters=cmd_filter))
    app.add_handler(CommandHandler("help", help_command, filters=cmd_filter))
    app.add_handler(CommandHandler("status", handle_status_command, filters=cmd_filter))
    app.add_handler(CommandHandler("metrics", handle_metrics_command, filters=cmd_filter))
    app.add_handler(CommandHandler("history", handle_history_command, filters=cmd_filter))
    app.add_handler(CommandHandler("schedule", handle_schedule_command, filters=cmd_filter))
    app.add_handler(CommandHandler("force", handle_force_command, filters=cmd_filter))
    app.add_handler(CommandHandler("learn", handle_learn_command, filters=cmd_filter))
    app.add_handler(CommandHandler("research", handle_research_command, filters=cmd_filter))
    app.add_handler(CommandHandler("pause", handle_pause_command, filters=cmd_filter))
    app.add_handler(CommandHandler("resume", handle_resume_command, filters=cmd_filter))
    app.add_handler(CommandHandler("config", handle_config_command, filters=cmd_filter))

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
        from bot.handlers.config_callbacks import handle_config_text_input

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
        except Exception as e:
            logger.error("Failed to send pipeline report section: %s", e)


def _build_research_section(viral_posts: list[dict]) -> str:
    hn_count = sum(1 for p in viral_posts if p.get("platform") == "hackernews")
    threads_count = sum(1 for p in viral_posts if p.get("platform") == "threads")

    lines = [f"🔍 <b>Research</b> (found {len(viral_posts)} viral posts)"]
    lines.append(f"Sources: {hn_count} from HackerNews, {threads_count} from Threads")

    sorted_posts = sorted(viral_posts, key=lambda p: p.get("engagement_rate", 0), reverse=True)
    lines.append("\nTop 3 by engagement:")
    for i, post in enumerate(sorted_posts[:3], 1):
        content = escape(post.get("content", "")[:80])
        er = post.get("engagement_rate", 0)
        likes = post.get("likes", 0)
        lines.append(f'  {i}. "{content}..." — {er:.1%} ER, {likes} likes')

    return "\n".join(lines)


def _build_patterns_section(patterns: list[dict]) -> str:
    lines = [f"🧩 <b>Patterns Extracted</b> ({len(patterns)} patterns)"]

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
    lines = [f"✍️ <b>Generated {len(variants)} Variants</b>"]

    for i, var in enumerate(variants[:5], 1):
        pattern = escape(var.get("pattern_used", "?"))
        pillar = escape(var.get("pillar", "?"))
        est = var.get("estimated_engagement", "unknown")
        content = escape(var.get("content", "")[:100])
        lines.append(f"  {i}. [{pattern}] [{pillar}] est: {est}")
        lines.append(f'     "{content}..."')

    return "\n".join(lines)


def _build_ranking_section(ranked: list[dict]) -> str:
    lines = ["📊 <b>Ranking</b> (AI x0.4 + History x0.3 + Novelty x0.3)"]

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
    except Exception as e:
        logger.warning("Failed to fetch recent metrics for enrichment: %s", e)

    try:
        pattern_name = selected_post.get("pattern_used", "")
        if pattern_name:
            perf = await kb.get_pattern_performance(pattern_name)
            enrichment["pattern_rationale"] = (
                f"{perf.avg_engagement_rate:.2%} avg ER over {perf.times_used} uses"
                if perf.times_used > 0
                else "New pattern (no history yet)"
            )
    except Exception as e:
        logger.warning("Failed to fetch pattern performance for enrichment: %s", e)

    try:
        strategy = await kb.get_strategy()
        if strategy.optimal_posting_times:
            enrichment["optimal_time"] = ", ".join(strategy.optimal_posting_times[:3])
    except Exception as e:
        logger.warning("Failed to fetch strategy for enrichment: %s", e)

    try:
        recent_posts = await kb.get_recent_posts(limit=10)
        if recent_posts:
            avg_score = sum(p.composite_score for p in recent_posts) / len(recent_posts)
            enrichment["avg_score"] = avg_score
    except Exception as e:
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

    message = (
        f"📝 <b>New Post for Approval</b> (Cycle #{cycle_number})\n"
        f"👥 Followers: {follower_count}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{content}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if enrichment and "avg_score" in enrichment:
        avg = enrichment["avg_score"]
        diff = score - avg
        sign = "+" if diff >= 0 else ""
        message += f"🎯 Score: <b>{score:.1f}/10</b> ({sign}{diff:.1f} vs avg {avg:.1f})\n"
    else:
        message += f"🎯 Score: <b>{score:.1f}/10</b>\n"

    if enrichment and "pattern_rationale" in enrichment:
        rationale = escape(enrichment["pattern_rationale"])
        message += f"🧩 Pattern: <b>{pattern}</b> — {rationale}\n"
    else:
        message += f"🧩 Pattern: <b>{pattern}</b>\n"

    if enrichment and "optimal_time" in enrichment:
        message += f"⏰ Best publish time: {escape(enrichment['optimal_time'])}\n"

    if enrichment and "recent_metrics" in enrichment:
        message += "\n📈 <b>Recent posts:</b>\n"
        for i, m in enumerate(enrichment["recent_metrics"][:3], 1):
            er = m["engagement_rate"]
            likes = m["likes"]
            replies = m["replies"]
            preview = escape(m["content_preview"])
            message += f'  {i}. {er:.2%} ER | {likes}L {replies}R | "{preview}..."\n'

    if alternatives:
        message += "\n<b>Alternatives:</b>\n"
        for i, alt in enumerate(alternatives, 1):
            alt_content = escape(alt.get("content", "")[:150])
            alt_pattern = escape(alt.get("pattern_used", "?"))
            message += (
                f"\n{i}. [{alt_pattern} | {alt.get('composite_score', 0):.1f}]\n{alt_content}...\n"
            )

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

    for i, _alt in enumerate(alternatives):
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
        parse_mode="HTML",
    )
