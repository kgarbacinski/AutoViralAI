import asyncio
import logging
from datetime import UTC, datetime
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from bot.dependencies import get_knowledge_base, get_orchestrator

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
        await update.message.reply_text("Knowledge base not available.")
        return

    lines = ["📊 <b>Performance Metrics</b>\n"]

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
                trend = "📈 up"
            elif avg_last_5 < avg_er:
                trend = "📉 down"
            else:
                trend = "➡️ flat"

            lines.append(f"Avg ER: {avg_er:.2%} (trend: {trend})")
            lines.append(f"Last 5 avg ER: {avg_last_5:.2%}")
            lines.append(f"Total: {all_views} views, {all_likes} likes, {all_replies} replies")
            lines.append(f"Posts tracked: {len(metrics_history)}")
        else:
            lines.append("No metrics collected yet.")
    except Exception as e:
        logger.error("Error fetching metrics: %s", e)
        lines.append("Error fetching metrics.")

    try:
        patterns = await kb.get_all_pattern_performances()
        if patterns:
            sorted_patterns = sorted(patterns, key=lambda p: p.effectiveness_score, reverse=True)
            lines.append("\n🧩 <b>Top Patterns:</b>")
            for i, p in enumerate(sorted_patterns[:3], 1):
                lines.append(
                    f"  {i}. <b>{escape(p.pattern_name)}</b> — "
                    f"{p.effectiveness_score:.1f}/10 "
                    f"({p.times_used} uses, {p.avg_engagement_rate:.2%} ER)"
                )
    except Exception as e:
        logger.error("Error fetching patterns: %s", e)

    try:
        strategy = await kb.get_strategy()
        if strategy.key_learnings:
            lines.append("\n🧠 <b>Key Learnings:</b>")
            for learning in strategy.key_learnings[:3]:
                lines.append(f"  • {escape(learning)}")
    except Exception as e:
        logger.error("Error fetching strategy: %s", e)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    if orchestrator.is_paused:
        await update.message.reply_text("Already paused.")
        return

    orchestrator.pause_all_jobs()
    await update.message.reply_text("All scheduled pipelines paused. Use /resume to restart.")


async def handle_resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    if not orchestrator.is_paused:
        await update.message.reply_text("Pipelines are already running.")
        return

    orchestrator.resume_all_jobs()
    await update.message.reply_text("All scheduled pipelines resumed.")


async def handle_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    kb = get_knowledge_base()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    lines = ["🗓 <b>Scheduled Jobs</b>\n"]

    jobs = orchestrator.get_scheduled_jobs()
    if jobs:
        for job in jobs:
            status = "⏸ paused" if job.get("paused") else "▶️ active"
            next_run = job.get("next_run_time", "N/A")
            lines.append(f"  {escape(job['id'])}: {status} | next: {next_run}")
    else:
        lines.append("  No jobs scheduled.")

    if kb:
        try:
            strategy = await kb.get_strategy()
            if strategy.optimal_posting_times:
                lines.append("\n⏰ <b>AI-Recommended Times:</b>")
                for t in strategy.optimal_posting_times:
                    lines.append(f"  {escape(t)}")
        except Exception as e:
            logger.error("Error fetching strategy for schedule: %s", e)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    try:
        posts = await kb.get_recent_posts(limit=10)
    except Exception as e:
        logger.error("Error fetching recent posts: %s", e)
        await update.message.reply_text("Error fetching post history.")
        return

    if not posts:
        await update.message.reply_text("No posts published yet.")
        return

    lines = ["📜 <b>Recent Posts</b>\n"]

    try:
        metrics_map = {}
        metrics_history = await kb.get_metrics_history(limit=50)
        for m in metrics_history:
            metrics_map[m.threads_id] = m
    except Exception:
        metrics_map = {}

    for i, post in enumerate(posts[:10], 1):
        preview = escape(post.content[:60].replace("\n", " "))
        pattern = escape(post.pattern_used)
        m = metrics_map.get(post.threads_id)
        if m:
            metrics_str = f"✅ {m.engagement_rate:.2%} ER | {m.likes}L {m.replies}R"
        else:
            metrics_str = "⏳ pending"
        lines.append(
            f"{i}. [<b>{pattern}</b>] {post.composite_score:.1f}/10\n"
            f'   "{preview}..."\n'
            f"   {post.published_at[:10]} | {metrics_str}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_force_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    if orchestrator.pending_approvals:
        await update.message.reply_text(
            "Cannot force: there are pending approvals. Approve or reject them first."
        )
        return

    active_tasks = sum(1 for t in _background_tasks if not t.done())
    if active_tasks >= MAX_CONCURRENT_BACKGROUND_TASKS:
        await update.message.reply_text(
            f"Too many tasks running ({active_tasks}). Wait for current tasks to finish."
        )
        return

    running_creation = any(
        t.get_name() == "force_creation" and not t.done() for t in _background_tasks
    )
    if running_creation:
        await update.message.reply_text("A creation pipeline is already running.")
        return

    await update.message.reply_text("⚡ Starting creation pipeline... This may take a few minutes.")

    async def _run_and_notify():
        try:
            await orchestrator.run_creation_pipeline()
        except Exception:
            logger.exception("Force creation pipeline failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text="Pipeline failed. Check server logs for details.",
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="force_creation"))


async def _build_learn_summary(kb) -> str:
    if not kb:
        return "Learning cycle completed. (Knowledge base not available)"

    parts = []

    try:
        pending = await kb.get_pending_metrics_posts()
        strategy = await kb.get_strategy()

        if strategy.key_learnings:
            parts.append("Learning cycle completed.\n")
            parts.append("Key learnings:")
            for learning in strategy.key_learnings[:5]:
                parts.append(f"  - {learning}")
            parts.append(f"\nStrategy iteration: {strategy.iteration}")
        elif pending:
            now = datetime.now(UTC)
            next_checks = []
            for post in pending[:3]:
                if post.scheduled_metrics_check:
                    check_time = datetime.fromisoformat(post.scheduled_metrics_check)
                    hours_left = max(0, (check_time - now).total_seconds() / 3600)
                    preview = post.content[:50] + "..." if len(post.content) > 50 else post.content
                    next_checks.append(f'  - "{preview}" ({hours_left:.0f}h left)')

            parts.append("Learning cycle completed — no metrics ready yet.\n")
            parts.append(f"Posts waiting for metrics check ({len(pending)}):")
            parts.extend(next_checks)
            parts.append("\nMetrics are collected 24h after publishing.")
            parts.append("Run /learn again after the check time passes.")
        else:
            parts.append(
                "Learning cycle completed — nothing to analyze.\n"
                "No published posts are pending metrics collection.\n"
                "Publish a post first, then wait 24h for /learn to gather insights."
            )
    except Exception:
        logger.exception("Failed to build learn summary")
        parts.append("Learning cycle completed. (Could not build detailed summary)")

    return "\n".join(parts)


async def handle_learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    await update.message.reply_text(
        "🧠 Starting learning cycle... Collecting metrics,"
        " analyzing performance, updating strategy."
    )

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
        except Exception:
            logger.exception("Learn command failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text="Learning pipeline failed. Check server logs for details.",
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="learn_pipeline"))


async def handle_research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    await update.message.reply_text("🔍 Running viral research... This may take a minute.")

    async def _run_and_notify():
        try:
            viral_posts = await orchestrator.run_research_only()

            if not viral_posts:
                text = "Research complete. No viral posts found."
            else:
                hn_count = sum(1 for p in viral_posts if p.get("platform") == "hackernews")
                threads_count = sum(1 for p in viral_posts if p.get("platform") == "threads")

                lines = [
                    f"Found {len(viral_posts)} viral posts ({hn_count} HN, {threads_count} Threads)"
                ]
                lines.append("\nTop by engagement:")

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
        except Exception:
            logger.exception("Research command failed")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text="Research failed. Check server logs for details.",
                )

    _track_task(asyncio.create_task(_run_and_notify(), name="research"))


async def handle_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    try:
        niche = await kb.get_niche_config()
    except Exception as e:
        logger.error("Error fetching niche config: %s", e)
        await update.message.reply_text("Error fetching configuration.")
        return

    if not niche:
        await update.message.reply_text("No configuration found. Run setup first.")
        return

    posting_times = (
        ", ".join(niche.preferred_posting_times) if niche.preferred_posting_times else "default"
    )

    avoid = escape(", ".join(niche.avoid_topics)) if niche.avoid_topics else "none"
    lines = [
        "🔧 <b>Current Configuration</b>\n",
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
