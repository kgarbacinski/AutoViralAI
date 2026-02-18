"""Command handlers for Telegram bot."""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.dependencies import get_knowledge_base, get_orchestrator

logger = logging.getLogger(__name__)


async def handle_metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /metrics — show performance metrics and top patterns."""
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    lines = ["*Performance Metrics*\n"]

    # Overall metrics
    try:
        metrics_history = await kb.get_metrics_history(limit=50)
        if metrics_history:
            all_er = [m.engagement_rate for m in metrics_history]
            all_likes = sum(m.likes for m in metrics_history)
            all_replies = sum(m.replies for m in metrics_history)
            all_views = sum(m.views for m in metrics_history)
            avg_er = sum(all_er) / len(all_er)

            # Trend: last 5 vs all
            last_5_er = [m.engagement_rate for m in metrics_history[:5]]
            avg_last_5 = sum(last_5_er) / len(last_5_er) if last_5_er else 0
            trend = "up" if avg_last_5 > avg_er else "down" if avg_last_5 < avg_er else "flat"

            lines.append(f"Avg ER: {avg_er:.2%} (trend: {trend})")
            lines.append(f"Last 5 avg ER: {avg_last_5:.2%}")
            lines.append(f"Total: {all_views} views, {all_likes} likes, {all_replies} replies")
            lines.append(f"Posts tracked: {len(metrics_history)}")
        else:
            lines.append("No metrics collected yet.")
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        lines.append("Error fetching metrics.")

    # Top patterns
    try:
        patterns = await kb.get_all_pattern_performances()
        if patterns:
            sorted_patterns = sorted(patterns, key=lambda p: p.effectiveness_score, reverse=True)
            lines.append("\n*Top Patterns:*")
            for i, p in enumerate(sorted_patterns[:3], 1):
                lines.append(
                    f"  {i}. {p.pattern_name} - "
                    f"{p.effectiveness_score:.1f}/10 "
                    f"({p.times_used} uses, {p.avg_engagement_rate:.2%} ER)"
                )
    except Exception as e:
        logger.error(f"Error fetching patterns: {e}")

    # Key learnings from strategy
    try:
        strategy = await kb.get_strategy()
        if strategy.key_learnings:
            lines.append("\n*Key Learnings:*")
            for learning in strategy.key_learnings[:3]:
                lines.append(f"  - {learning}")
    except Exception as e:
        logger.error(f"Error fetching strategy: {e}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pause — pause all scheduled pipelines."""
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
    """Handle /resume — resume all scheduled pipelines."""
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
    """Handle /schedule — show scheduled jobs and optimal times."""
    orchestrator = get_orchestrator()
    kb = get_knowledge_base()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    lines = ["*Scheduled Jobs*\n"]

    jobs = orchestrator.get_scheduled_jobs()
    if jobs:
        for job in jobs:
            status = "paused" if job.get("paused") else "active"
            next_run = job.get("next_run_time", "N/A")
            lines.append(f"  {job['id']}: {status} | next: {next_run}")
    else:
        lines.append("  No jobs scheduled.")

    # AI-recommended times from strategy
    if kb:
        try:
            strategy = await kb.get_strategy()
            if strategy.optimal_posting_times:
                lines.append("\n*AI-Recommended Times:*")
                for t in strategy.optimal_posting_times:
                    lines.append(f"  {t}")
        except Exception as e:
            logger.error(f"Error fetching strategy for schedule: {e}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — last 10 published posts."""
    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    try:
        posts = await kb.get_recent_posts(limit=10)
    except Exception as e:
        logger.error(f"Error fetching recent posts: {e}")
        await update.message.reply_text("Error fetching post history.")
        return

    if not posts:
        await update.message.reply_text("No posts published yet.")
        return

    lines = ["*Recent Posts*\n"]

    # Get metrics for comparison
    try:
        metrics_map = {}
        metrics_history = await kb.get_metrics_history(limit=50)
        for m in metrics_history:
            metrics_map[m.threads_id] = m
    except Exception:
        metrics_map = {}

    for i, post in enumerate(posts[:10], 1):
        preview = post.content[:60].replace("\n", " ")
        m = metrics_map.get(post.threads_id)
        if m:
            metrics_str = f"{m.engagement_rate:.2%} ER | {m.likes}L {m.replies}R"
        else:
            metrics_str = "pending"
        lines.append(
            f"{i}. [{post.pattern_used}] {post.composite_score:.1f}/10\n"
            f'   "{preview}..."\n'
            f"   {post.published_at[:10]} | {metrics_str}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_force_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /force — trigger creation pipeline immediately."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    if orchestrator.pending_approvals:
        await update.message.reply_text(
            "Cannot force: there are pending approvals. Approve or reject them first."
        )
        return

    await update.message.reply_text("Starting creation pipeline... This may take a few minutes.")
    asyncio.create_task(orchestrator.run_creation_pipeline())


async def handle_learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /learn — manually trigger the learning pipeline."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    await update.message.reply_text(
        "Starting learning cycle... Collecting metrics, analyzing performance, updating strategy."
    )

    async def _run_and_notify():
        try:
            await orchestrator.run_learning_pipeline()
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                # Send summary after completion
                kb = get_knowledge_base()
                summary = "Learning cycle completed."
                if kb:
                    try:
                        strategy = await kb.get_strategy()
                        parts = [summary]
                        if strategy.key_learnings:
                            parts.append("\nKey learnings:")
                            for learning in strategy.key_learnings[:3]:
                                parts.append(f"  - {learning}")
                        parts.append(f"\nStrategy iteration: {strategy.iteration}")
                        summary = "\n".join(parts)
                    except Exception:
                        pass
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=summary,
                )
        except Exception as e:
            logger.error(f"Learn command failed: {e}")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=f"Learning pipeline failed: {e}",
                )

    asyncio.create_task(_run_and_notify())


async def handle_research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /research — run standalone viral research."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        await update.message.reply_text("Orchestrator not available.")
        return

    await update.message.reply_text("Running viral research... This may take a minute.")

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

            await orchestrator.bot_app.bot.send_message(
                chat_id=orchestrator.telegram_chat_id,
                text=text,
            )
        except Exception as e:
            logger.error(f"Research command failed: {e}")
            if orchestrator.bot_app and orchestrator.telegram_chat_id:
                await orchestrator.bot_app.bot.send_message(
                    chat_id=orchestrator.telegram_chat_id,
                    text=f"Research failed: {e}",
                )

    asyncio.create_task(_run_and_notify())


async def handle_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /config — show current config with edit buttons."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    kb = get_knowledge_base()
    if not kb:
        await update.message.reply_text("Knowledge base not available.")
        return

    try:
        niche = await kb.get_niche_config()
    except Exception as e:
        logger.error(f"Error fetching niche config: {e}")
        await update.message.reply_text("Error fetching configuration.")
        return

    if not niche:
        await update.message.reply_text("No configuration found. Run setup first.")
        return

    posting_times = (
        ", ".join(niche.preferred_posting_times) if niche.preferred_posting_times else "default"
    )

    lines = [
        "*Current Configuration*\n",
        f"Tone: {niche.voice.tone}",
        f"Persona: {niche.voice.persona}",
        f"Language: {niche.voice.language}",
        f"Max hashtags: {niche.max_hashtags_per_post}",
        f"Max posts/day: {niche.max_posts_per_day}",
        f"Posting times: {posting_times}",
        f"Avoid topics: {', '.join(niche.avoid_topics) if niche.avoid_topics else 'none'}",
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
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
