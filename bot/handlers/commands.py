import asyncio
import logging
from datetime import UTC, datetime
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.dependencies import get_knowledge_base, get_orchestrator
from bot.messages import (
    ALREADY_PAUSED,
    ALREADY_RUNNING,
    CONFIG_FETCH_ERROR,
    CONFIG_HEADER,
    CONFIG_NOT_FOUND,
    FORCE_ALREADY_RUNNING,
    FORCE_PENDING_APPROVALS,
    FORCE_STARTED,
    FORCE_TOO_MANY_TASKS,
    HISTORY_FETCH_ERROR,
    HISTORY_HEADER,
    HISTORY_METRICS_PENDING,
    HISTORY_NO_POSTS,
    KB_NOT_AVAILABLE,
    LEARN_COMPLETED,
    LEARN_COMPLETED_KB_UNAVAILABLE,
    LEARN_COMPLETED_SUMMARY_ERROR,
    LEARN_KEY_LEARNINGS,
    LEARN_METRICS_DELAY,
    LEARN_NO_METRICS_YET,
    LEARN_NOTHING_TO_ANALYZE,
    LEARN_PIPELINE_FAILED,
    LEARN_POSTS_WAITING,
    LEARN_RUN_AGAIN,
    LEARN_STARTED,
    LEARN_STRATEGY_ITERATION,
    METRICS_AVG_ER,
    METRICS_ERROR,
    METRICS_HEADER,
    METRICS_KEY_LEARNINGS_HEADER,
    METRICS_LAST_5_ER,
    METRICS_NONE,
    METRICS_POSTS_TRACKED,
    METRICS_TOP_PATTERNS_HEADER,
    METRICS_TOTALS,
    METRICS_TREND_DOWN,
    METRICS_TREND_FLAT,
    METRICS_TREND_UP,
    ORCHESTRATOR_NOT_AVAILABLE,
    PAUSED_SUCCESS,
    PIPELINE_FAILED,
    RESEARCH_FAILED,
    RESEARCH_FOUND,
    RESEARCH_NO_RESULTS,
    RESEARCH_STARTED,
    RESEARCH_TOP_BY_ENGAGEMENT,
    RESUMED_SUCCESS,
    SCHEDULE_AI_TIMES_HEADER,
    SCHEDULE_HEADER,
    SCHEDULE_NO_JOBS,
)
from src.exceptions import KnowledgeBaseError, PipelineError

logger = logging.getLogger(__name__)

MAX_CONCURRENT_BACKGROUND_TASKS = 3

_background_tasks: set[asyncio.Task] = set()


async def cancel_background_tasks() -> None:
    tasks = list(_background_tasks)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _background_tasks.clear()


def _track_task(task: asyncio.Task) -> None:
    _background_tasks.add(task)

    def _on_done(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        if not t.cancelled() and t.exception():
            logger.error("Background task %s failed: %s", t.get_name(), t.exception())

    task.add_done_callback(_on_done)


async def handle_metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text(KB_NOT_AVAILABLE)
        return

    lines = [METRICS_HEADER]

    try:
        metrics_history = await kb.get_metrics_history(limit=50)
        if metrics_history:
            all_er = [m.engagement_rate for m in metrics_history]
            all_likes = sum(m.likes for m in metrics_history)
            all_replies = sum(m.replies for m in metrics_history)
            all_views = sum(m.views for m in metrics_history)
            avg_er = sum(all_er) / len(all_er)

            last_5_er = [m.engagement_rate for m in metrics_history[:5]]
            avg_last_5 = sum(last_5_er) / len(last_5_er) if last_5_er else 0
            if avg_last_5 > avg_er:
                trend = METRICS_TREND_UP
            elif avg_last_5 < avg_er:
                trend = METRICS_TREND_DOWN
            else:
                trend = METRICS_TREND_FLAT

            lines.append(METRICS_AVG_ER.format(avg_er=avg_er, trend=trend))
            lines.append(METRICS_LAST_5_ER.format(avg_last_5=avg_last_5))
            lines.append(
                METRICS_TOTALS.format(views=all_views, likes=all_likes, replies=all_replies)
            )
            lines.append(METRICS_POSTS_TRACKED.format(count=len(metrics_history)))
        else:
            lines.append(METRICS_NONE)
    except KnowledgeBaseError as e:
        logger.error("Error fetching metrics: %s", e)
        lines.append(METRICS_ERROR)

    try:
        patterns = await kb.get_all_pattern_performances()
        if patterns:
            sorted_patterns = sorted(patterns, key=lambda p: p.effectiveness_score, reverse=True)
            lines.append(METRICS_TOP_PATTERNS_HEADER)
            for i, p in enumerate(sorted_patterns[:3], 1):
                lines.append(
                    f"  {i}. <b>{escape(p.pattern_name)}</b> — "
                    f"{p.effectiveness_score:.1f}/10 "
                    f"({p.times_used} uses, {p.avg_engagement_rate:.2%} ER)"
                )
    except KnowledgeBaseError as e:
        logger.error("Error fetching patterns: %s", e)

    try:
        strategy = await kb.get_strategy()
        if strategy.key_learnings:
            lines.append(METRICS_KEY_LEARNINGS_HEADER)
            for learning in strategy.key_learnings[:3]:
                lines.append(f"  • {escape(learning)}")
    except KnowledgeBaseError as e:
        logger.error("Error fetching strategy: %s", e)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    if orchestrator.is_paused:
        await update.message.reply_text(ALREADY_PAUSED)
        return

    orchestrator.pause_all_jobs()
    await update.message.reply_text(PAUSED_SUCCESS)


async def handle_resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    if not orchestrator.is_paused:
        await update.message.reply_text(ALREADY_RUNNING)
        return

    orchestrator.resume_all_jobs()
    await update.message.reply_text(RESUMED_SUCCESS)


async def handle_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    kb = get_knowledge_base()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    lines = [SCHEDULE_HEADER]

    jobs = orchestrator.get_scheduled_jobs()
    if jobs:
        for job in jobs:
            status = "⏸ paused" if job.get("paused") else "▶️ active"
            next_run = job.get("next_run_time", "N/A")
            lines.append(f"  {escape(job['id'])}: {status} | next: {next_run}")
    else:
        lines.append(SCHEDULE_NO_JOBS)

    if kb:
        try:
            strategy = await kb.get_strategy()
            if strategy.optimal_posting_times:
                lines.append(SCHEDULE_AI_TIMES_HEADER)
                for t in strategy.optimal_posting_times:
                    lines.append(f"  {escape(t)}")
        except KnowledgeBaseError as e:
            logger.error("Error fetching strategy for schedule: %s", e)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text(KB_NOT_AVAILABLE)
        return

    try:
        posts = await kb.get_recent_posts(limit=10)
    except KnowledgeBaseError as e:
        logger.error("Error fetching recent posts: %s", e)
        await update.message.reply_text(HISTORY_FETCH_ERROR)
        return

    if not posts:
        await update.message.reply_text(HISTORY_NO_POSTS)
        return

    lines = [HISTORY_HEADER]

    try:
        metrics_map = {}
        metrics_history = await kb.get_metrics_history(limit=50)
        for m in metrics_history:
            metrics_map[m.threads_id] = m
    except KnowledgeBaseError:
        metrics_map = {}

    for i, post in enumerate(posts[:10], 1):
        preview = escape(post.content[:60].replace("\n", " "))
        pattern = escape(post.pattern_used)
        m = metrics_map.get(post.threads_id)
        if m:
            metrics_str = f"✅ {m.engagement_rate:.2%} ER | {m.likes}L {m.replies}R"
        else:
            metrics_str = HISTORY_METRICS_PENDING
        lines.append(
            f"{i}. [<b>{pattern}</b>] {post.composite_score:.1f}/10\n"
            f'   "{preview}..."\n'
            f"   {post.published_at[:10]} | {metrics_str}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_force_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    if orchestrator.pending_approvals:
        await update.message.reply_text(FORCE_PENDING_APPROVALS)
        return

    active_tasks = sum(1 for t in _background_tasks if not t.done())
    if active_tasks >= MAX_CONCURRENT_BACKGROUND_TASKS:
        await update.message.reply_text(FORCE_TOO_MANY_TASKS.format(active_tasks=active_tasks))
        return

    running_creation = any(
        t.get_name() == "force_creation" and not t.done() for t in _background_tasks
    )
    if running_creation:
        await update.message.reply_text(FORCE_ALREADY_RUNNING)
        return

    await update.message.reply_text(FORCE_STARTED)

    async def _run_and_notify():
        try:
            await orchestrator.run_creation_pipeline()
        except PipelineError:
            logger.exception("Force creation pipeline failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=PIPELINE_FAILED,
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="force_creation"))


async def _build_learn_summary(kb) -> str:
    if not kb:
        return LEARN_COMPLETED_KB_UNAVAILABLE

    parts = []

    try:
        pending = await kb.get_pending_metrics_posts()
        strategy = await kb.get_strategy()

        if strategy.key_learnings:
            parts.append(LEARN_COMPLETED)
            parts.append(LEARN_KEY_LEARNINGS)
            for learning in strategy.key_learnings[:5]:
                parts.append(f"  - {learning}")
            parts.append(LEARN_STRATEGY_ITERATION.format(iteration=strategy.iteration))
        elif pending:
            now = datetime.now(UTC)
            next_checks = []
            for post in pending[:3]:
                if post.scheduled_metrics_check:
                    check_time = datetime.fromisoformat(post.scheduled_metrics_check)
                    hours_left = max(0, (check_time - now).total_seconds() / 3600)
                    preview = post.content[:50] + "..." if len(post.content) > 50 else post.content
                    next_checks.append(f'  - "{preview}" ({hours_left:.0f}h left)')

            parts.append(LEARN_NO_METRICS_YET)
            parts.append(LEARN_POSTS_WAITING.format(count=len(pending)))
            parts.extend(next_checks)
            parts.append(LEARN_METRICS_DELAY)
            parts.append(LEARN_RUN_AGAIN)
        else:
            parts.append(LEARN_NOTHING_TO_ANALYZE)
    except KnowledgeBaseError:
        logger.exception("Failed to build learn summary")
        parts.append(LEARN_COMPLETED_SUMMARY_ERROR)

    return "\n".join(parts)


async def handle_learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    await update.message.reply_text(LEARN_STARTED)

    async def _run_and_notify():
        try:
            await orchestrator.run_learning_pipeline()
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                kb = get_knowledge_base()
                summary = await _build_learn_summary(kb)
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=summary,
                )
        except (PipelineError, TelegramError):
            logger.exception("Learn command failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=LEARN_PIPELINE_FAILED,
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="learn_pipeline"))


async def handle_research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text(ORCHESTRATOR_NOT_AVAILABLE)
        return

    await update.message.reply_text(RESEARCH_STARTED)

    async def _run_and_notify():
        try:
            viral_posts = await orchestrator.run_research_only()

            if not viral_posts:
                text = RESEARCH_NO_RESULTS
            else:
                hn_count = sum(1 for p in viral_posts if p.get("platform") == "hackernews")
                threads_count = sum(1 for p in viral_posts if p.get("platform") == "threads")

                lines = [
                    RESEARCH_FOUND.format(
                        total=len(viral_posts), hn=hn_count, threads=threads_count
                    )
                ]
                lines.append(RESEARCH_TOP_BY_ENGAGEMENT)

                sorted_posts = sorted(
                    viral_posts,
                    key=lambda p: p.get("engagement_rate", 0),
                    reverse=True,
                )
                for i, post in enumerate(sorted_posts[:7], 1):
                    platform = post.get("platform", "?")
                    content = post.get("content", "")[:80]
                    er = post.get("engagement_rate", 0)
                    likes = post.get("likes", 0)
                    lines.append(f'  {i}. [{platform}] "{content}..." - {er:.1%} ER, {likes} likes')

                text = "\n".join(lines)

            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=text,
                )
        except (KnowledgeBaseError, TelegramError):
            logger.exception("Research command failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=RESEARCH_FAILED,
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="research"))


async def handle_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text(KB_NOT_AVAILABLE)
        return

    try:
        niche = await kb.get_niche_config()
    except KnowledgeBaseError as e:
        logger.error("Error fetching niche config: %s", e)
        await update.message.reply_text(CONFIG_FETCH_ERROR)
        return

    if not niche:
        await update.message.reply_text(CONFIG_NOT_FOUND)
        return

    posting_times = (
        ", ".join(niche.preferred_posting_times) if niche.preferred_posting_times else "default"
    )

    avoid = escape(", ".join(niche.avoid_topics)) if niche.avoid_topics else "none"
    lines = [
        CONFIG_HEADER,
        f"Tone: {escape(niche.voice.tone)}",
        f"Persona: {escape(niche.voice.persona)}",
        f"Language: {escape(niche.voice.language)}",
        f"Max hashtags: {niche.max_hashtags_per_post}",
        f"Max posts/day: {niche.max_posts_per_day}",
        f"Posting times: {escape(posting_times)}",
        f"Avoid topics: {avoid}",
    ]

    keyboard = [
        [
            InlineKeyboardButton("Tone", callback_data="cfg:tone"),
            InlineKeyboardButton("Language", callback_data="cfg:language"),
        ],
        [
            InlineKeyboardButton("Max Hashtags", callback_data="cfg:hashtags"),
            InlineKeyboardButton("Max Posts/Day", callback_data="cfg:max_posts"),
        ],
        [
            InlineKeyboardButton("Posting Schedule", callback_data="cfg:schedule"),
            InlineKeyboardButton("Avoid Topics", callback_data="cfg:avoid"),
        ],
    ]

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
