# --- Common ---
KB_NOT_AVAILABLE = "Knowledge base not available."
ORCHESTRATOR_NOT_AVAILABLE = "Orchestrator not available."

# --- Commands: /metrics ---
METRICS_HEADER = "📊 <b>Performance Metrics</b>\n"
METRICS_TREND_UP = "📈 up"
METRICS_TREND_DOWN = "📉 down"
METRICS_TREND_FLAT = "➡️ flat"
METRICS_AVG_ER = "Avg ER: {avg_er:.2%} (trend: {trend})"
METRICS_LAST_5_ER = "Last 5 avg ER: {avg_last_5:.2%}"
METRICS_TOTALS = "Total: {views} views, {likes} likes, {replies} replies"
METRICS_POSTS_TRACKED = "Posts tracked: {count}"
METRICS_NONE = "No metrics collected yet."
METRICS_ERROR = "Error fetching metrics."
METRICS_TOP_PATTERNS_HEADER = "\n🧩 <b>Top Patterns:</b>"
METRICS_KEY_LEARNINGS_HEADER = "\n🧠 <b>Key Learnings:</b>"

# --- Commands: /pause, /resume ---
ALREADY_PAUSED = "Already paused."
PAUSED_SUCCESS = "All scheduled pipelines paused. Use /resume to restart."
ALREADY_RUNNING = "Pipelines are already running."
RESUMED_SUCCESS = "All scheduled pipelines resumed."

# --- Commands: /schedule ---
SCHEDULE_HEADER = "🗓 <b>Scheduled Jobs</b>\n"
SCHEDULE_NO_JOBS = "  No jobs scheduled."
SCHEDULE_AI_TIMES_HEADER = "\n⏰ <b>AI-Recommended Times:</b>"

# --- Commands: /history ---
HISTORY_HEADER = "📜 <b>Recent Posts</b>\n"
HISTORY_FETCH_ERROR = "Error fetching post history."
HISTORY_NO_POSTS = "No posts published yet."
HISTORY_METRICS_PENDING = "⏳ pending"

# --- Commands: /force ---
FORCE_PENDING_APPROVALS = "Cannot force: there are pending approvals. Approve or reject them first."
FORCE_TOO_MANY_TASKS = "Too many tasks running ({active_tasks}). Wait for current tasks to finish."
FORCE_ALREADY_RUNNING = "A creation pipeline is already running."
FORCE_STARTED = "⚡ Starting creation pipeline... This may take a few minutes."
PIPELINE_FAILED = "Pipeline failed. Check server logs for details."

# --- Commands: /learn ---
LEARN_STARTED = (
    "🧠 Starting learning cycle... Collecting metrics, analyzing performance, updating strategy."
)
LEARN_COMPLETED = "Learning cycle completed.\n"
LEARN_COMPLETED_KB_UNAVAILABLE = "Learning cycle completed. (Knowledge base not available)"
LEARN_COMPLETED_SUMMARY_ERROR = "Learning cycle completed. (Could not build detailed summary)"
LEARN_KEY_LEARNINGS = "Key learnings:"
LEARN_STRATEGY_ITERATION = "\nStrategy iteration: {iteration}"
LEARN_NO_METRICS_YET = "Learning cycle completed — no metrics ready yet.\n"
LEARN_POSTS_WAITING = "Posts waiting for metrics check ({count}):"
LEARN_METRICS_DELAY = "\nMetrics are collected 24h after publishing."
LEARN_RUN_AGAIN = "Run /learn again after the check time passes."
LEARN_NOTHING_TO_ANALYZE = (
    "Learning cycle completed — nothing to analyze.\n"
    "No published posts are pending metrics collection.\n"
    "Publish a post first, then wait 24h for /learn to gather insights."
)
LEARN_PIPELINE_FAILED = "Learning pipeline failed. Check server logs for details."

# --- Commands: /research ---
RESEARCH_STARTED = "🔍 Running viral research... This may take a minute."
RESEARCH_NO_RESULTS = "Research complete. No viral posts found."
RESEARCH_FOUND = "Found {total} viral posts ({hn} HN, {threads} Threads)"
RESEARCH_TOP_BY_ENGAGEMENT = "\nTop by engagement:"
RESEARCH_FAILED = "Research failed. Check server logs for details."

# --- Commands: /config ---
CONFIG_HEADER = "🔧 <b>Current Configuration</b>\n"
CONFIG_FETCH_ERROR = "Error fetching configuration."
CONFIG_NOT_FOUND = "No configuration found. Run setup first."

# --- Approval ---
UNAUTHORIZED = "Unauthorized."
INVALID_CALLBACK = "Invalid callback data."
APPROVED_SUFFIX = "\n\n--- APPROVED ---"
REJECT_PROMPT_SUFFIX = "\n\n--- Why reject? ---"
REJECT_TYPE_REASON = "Type your rejection reason:"
REJECTED_SUFFIX = "\n\n--- REJECTED: {feedback} ---"
EDIT_MODE_SUFFIX = "\n\n--- EDIT MODE ---\nPlease send the edited post text as a reply."
APPROVED_ALT_SUFFIX = "\n\n--- APPROVED (Alt {index}) ---"
SCHEDULE_PROMPT_SUFFIX = "\n\n--- When to publish? ---"
SCHEDULED_SUFFIX = "\n\n--- SCHEDULED: {time} UTC ---"
UNKNOWN_ACTION = "Unknown action."
POST_TOO_LONG = "Post too long (max {max_length} characters for Threads). Try again."
EDIT_RECEIVED = "Edited post received. Publishing..."
FEEDBACK_TOO_LONG = "Feedback too long (max {max_length} characters). Try again."
REJECTION_FEEDBACK_RECEIVED = "Rejection feedback received: {feedback}"

# --- Status ---
STATUS_HEADER = "🤖 <b>AutoViralAI Status</b>\n"
STATUS_PAUSED = "🟡 Paused"
STATUS_RUNNING = "🟢 Running"
STATUS_ORCHESTRATOR_UNAVAILABLE = "State: Orchestrator not available"

# --- Config callbacks ---
CONFIG_SELECT_TONE = "Select tone:"
CONFIG_SELECT_LANGUAGE = "Select language:"
CONFIG_MAX_HASHTAGS = "Max hashtags per post:"
CONFIG_MAX_POSTS_PER_DAY = "Max posts per day:"
CONFIG_AVOID_TOPICS = "Avoid topics:"
CONFIG_SELECT_SCHEDULE = (
    "Select posting hours (pick one at a time, re-open /config to add more).\n"
    "Current schedule will be replaced."
)
CONFIG_NO_CONFIG = "No config found."
CONFIG_TONE_UPDATED = "Tone updated to: {value}"
CONFIG_LANGUAGE_UPDATED = "Language updated to: {value}"
CONFIG_INVALID_HASHTAGS = "Invalid value for max hashtags."
CONFIG_HASHTAGS_UPDATED = "Max hashtags updated to: {value}"
CONFIG_INVALID_MAX_POSTS = "Invalid value for max posts."
CONFIG_MAX_POSTS_UPDATED = "Max posts/day updated to: {value}"
CONFIG_AVOID_CLEARED = "Avoid topics cleared."
CONFIG_TYPE_AVOID_TOPIC = "Type the topic to avoid:"
CONFIG_SCHEDULE_UPDATED = "Schedule updated. Posting times: {times}\nJobs have been rescheduled."
CONFIG_UPDATE_FAILED = "Failed to update config. Check server logs for details."
CONFIG_INVALID_SCHEDULE = "Invalid schedule value."
CONFIG_INPUT_TOO_LONG = "Input too long (max 200 characters). Try again."
CONFIG_AVOID_TOPIC_ADDED = "Added '{topic}' to avoid topics.\nCurrent: {current}"
CONFIG_ADD_TOPIC_FAILED = "Failed to add topic. Check server logs for details."

# --- Telegram bot: core ---
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
START_MESSAGE = (
    "AutoViralAI Bot active.\n\n"
    "Type /help to see all available commands.\n\n"
    "I'll send you posts for approval when they're ready."
)

# --- Pipeline report sections ---
REPORT_RESEARCH_HEADER = "🔍 <b>Research</b> (found {count} viral posts)"
REPORT_RESEARCH_SOURCES = "Sources: {hn} from HackerNews, {threads} from Threads"
REPORT_TOP_BY_ENGAGEMENT = "\nTop 3 by engagement:"
REPORT_PATTERNS_HEADER = "🧩 <b>Patterns Extracted</b> ({count} patterns)"
REPORT_GENERATION_HEADER = "✍️ <b>Generated {count} Variants</b>"
REPORT_RANKING_HEADER = "📊 <b>Ranking</b> (AI x0.4 + History x0.3 + Novelty x0.3)"

# --- Approval request ---
APPROVAL_REQUEST_HEADER = (
    "📝 <b>New Post for Approval</b> (Cycle #{cycle})\n"
    "👥 Followers: {followers}\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "{content}\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
)
APPROVAL_SCORE = "🎯 Score: <b>{score:.1f}/10</b>\n"
APPROVAL_SCORE_WITH_AVG = "🎯 Score: <b>{score:.1f}/10</b> ({sign}{diff:.1f} vs avg {avg:.1f})\n"
APPROVAL_PATTERN = "🧩 Pattern: <b>{pattern}</b>\n"
APPROVAL_PATTERN_WITH_RATIONALE = "🧩 Pattern: <b>{pattern}</b> — {rationale}\n"
APPROVAL_BEST_TIME = "⏰ Best publish time: {time}\n"
APPROVAL_RECENT_POSTS_HEADER = "\n📈 <b>Recent posts:</b>\n"
APPROVAL_ALTERNATIVES_HEADER = "\n<b>Alternatives:</b>\n"
APPROVAL_ALTERNATIVE_MSG = (
    "💡 <b>Alternative {index}</b> (Cycle #{cycle})\n"
    "🧩 {pattern} | 🎯 {score:.1f}/10\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "{content}\n"
    "━━━━━━━━━━━━━━━━━━━━"
)
ENRICHMENT_NEW_PATTERN = "New pattern (no history yet)"
ENRICHMENT_PATTERN_RATIONALE = "{avg_er:.2%} avg ER over {times_used} uses"

# --- Creation pipeline failure ---
CREATION_PIPELINE_FAILED_NOTIFY = (
    "❌ <b>Creation Pipeline Failed</b> (Cycle #{cycle})\n\n"
    "Pipeline completed but could not generate a post.\n\n"
    "<b>Errors:</b>\n{errors}\n\n"
    "Next scheduled run: {next_run}"
)
