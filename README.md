<div align="center">

# self-learning-viral-agent

**An autonomous AI agent that grows your Threads account by researching viral content, generating posts, and continuously learning from what works.**

Built with [LangGraph](https://github.com/langchain-ai/langgraph) &bull; Powered by Claude &bull; Human-in-the-loop via Telegram

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)](#tests)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3+-orange.svg)](https://github.com/langchain-ai/langgraph)

</div>

---

Most social media bots just post on a schedule. This agent **learns**. It studies what goes viral in your niche, extracts the patterns behind it, generates posts using those patterns, publishes them, measures the results, and feeds everything back into its strategy. Every cycle makes it smarter.

```
Day 1:  "Here's a generic coding tip"           → 12 likes
Day 7:  "Hot take: most devs don't need Docker"  → 340 likes
Day 14: Agent learned contrarian hooks work 3x    → adapts strategy automatically
```

## How It Works

The system runs two independent pipelines that share a knowledge base:

```mermaid
graph TB
    subgraph "Pipeline 1: Content Creation (runs 2-3x/day)"
        A[Goal Check] -->|not reached| B[Research Viral Content]
        A -->|100 followers reached| Z[Done!]
        B --> C[Extract Patterns]
        C --> D[Generate 5 Post Variants]
        D --> E[Multi-Signal Ranking]
        E --> F{Human Approval<br/>via Telegram}
        F -->|Approve/Edit| G[Publish to Threads]
        F -->|Reject| D
        G --> H[Schedule Metrics Check]
    end

    subgraph "Pipeline 2: Learning Loop (runs daily)"
        I[Collect Metrics] --> J[Analyze Performance]
        J --> K[Update Pattern Scores]
        K --> L[Adjust Strategy]
    end

    H -.->|shared knowledge base| I
    L -.->|improved strategy| B

    style A fill:#4A90D9,stroke:#333,color:#fff
    style F fill:#E8A838,stroke:#333,color:#fff
    style G fill:#50C878,stroke:#333,color:#fff
    style L fill:#9B59B6,stroke:#333,color:#fff
    style Z fill:#50C878,stroke:#333,color:#fff
```

### Why Two Pipelines?

Posts need **24-48 hours** to accumulate meaningful engagement data. You can't research, post, and learn in one loop. The creation pipeline runs multiple times per day, while the learning pipeline runs once daily on yesterday's data — then feeds improved strategy back into creation.

## The Self-Learning Loop

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Research         What's going viral right now?        │
│      ↓                                                  │
│   Extract          Why is it going viral?               │
│      ↓             (patterns, hooks, structures)        │
│   Generate         Create posts using those patterns    │
│      ↓                                                  │
│   Rank             AI score + historical data + novelty │
│      ↓                                                  │
│   Publish          Post the winner                      │
│      ↓                                                  │
│   Measure          Wait 24h, collect engagement data    │
│      ↓                                                  │
│   Learn            What worked? What didn't? Why?       │
│      ↓                                                  │
│   Adapt            Update strategy, adjust weights      │
│      │                                                  │
│      └──────────── Feed back into Research ─────────────│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Multi-Signal Ranking

Posts aren't ranked by AI vibes alone. Each variant gets a **composite score** from three independent signals:

```
composite = 0.4 × ai_score + 0.3 × pattern_history + 0.3 × novelty
```

| Signal | What it measures | How |
|--------|-----------------|-----|
| **AI Score** (0-10) | Viral potential: hook strength, emotional trigger, shareability | Claude evaluates each variant |
| **Pattern History** (0-10) | How well this pattern performed in the past | Cumulative engagement data from knowledge base |
| **Novelty** (0-10) | How different this is from recent posts | Cosine distance of embeddings vs last 20 posts |

New patterns get a **5.0 exploration bonus** for history score — the system balances exploitation (use what works) with exploration (try new things).

## Human-in-the-Loop

The agent never posts without your approval. When a post is ready:

```
┌──────────────────────────────────────────┐
│  📱 Telegram Bot                         │
│                                          │
│  New Post for Approval (Cycle #7)        │
│  Followers: 43                           │
│  ─────────────────────────────           │
│  Hot take: 90% of "clean code"           │
│  advice makes your code slower.          │
│                                          │
│  The fastest code is the code that       │
│  doesn't exist. Ship less, ship faster.  │
│  ─────────────────────────────           │
│  Pattern: contrarian_hot_take            │
│  Score: 7.8/10                           │
│                                          │
│  [✅ Approve] [✏️ Edit] [❌ Reject]       │
│                                          │
│  Alternatives:                           │
│  [📝 Use Alt 1]  [📝 Use Alt 2]          │
└──────────────────────────────────────────┘
```

Built on LangGraph's `interrupt()` mechanism — the graph pauses, saves state, and resumes when you respond. Even if the server restarts.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/self-learning-viral-agent.git
cd self-learning-viral-agent

# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY (minimum required)
```

### Run Your First Cycle

```bash
# Interactive mode — you approve/reject posts in the terminal
uv run python scripts/manual_run.py

# Auto-approve mode (for testing the full pipeline)
uv run python scripts/manual_run.py --auto-approve

# Run the learning pipeline
uv run python scripts/manual_run.py --pipeline learning
```

The first run uses **mock APIs** — no Threads account needed. You'll see the full pipeline execute with fake but realistic data.

### Health Check

```bash
uv run python scripts/check_health.py
```

## Architecture

```
self-learning-viral-agent/
├── config/
│   ├── account_niche.yaml       # Your niche, voice, audience, content pillars
│   └── settings.py              # Environment config (pydantic-settings)
│
├── src/
│   ├── models/                  # Pydantic models + TypedDict states
│   │   ├── state.py             # Graph state schemas (the data flowing through)
│   │   ├── research.py          # ViralPost, ContentPattern
│   │   ├── content.py           # PostVariant, RankedPost
│   │   ├── publishing.py        # PublishedPost, PostMetrics
│   │   └── strategy.py          # AccountNiche, ContentStrategy, PatternPerformance
│   │
│   ├── graphs/                  # LangGraph pipeline definitions
│   │   ├── creation_pipeline.py # Graph 1: research → generate → approve → publish
│   │   └── learning_pipeline.py # Graph 2: metrics → analyze → learn → adapt
│   │
│   ├── nodes/                   # Individual pipeline steps
│   │   ├── goal_check.py        # Check follower count vs target
│   │   ├── research.py          # Find viral content (Reddit + Threads)
│   │   ├── patterns.py          # LLM extracts reusable patterns
│   │   ├── generation.py        # LLM generates 5 post variants
│   │   ├── ranking.py           # Multi-signal scoring (AI + history + novelty)
│   │   ├── approval.py          # Human-in-the-loop via interrupt()
│   │   ├── publishing.py        # Publish to Threads API
│   │   ├── metrics.py           # Collect engagement data
│   │   ├── analysis.py          # LLM analyzes what worked
│   │   ├── learning.py          # Update pattern performance records
│   │   └── strategy.py          # LLM adjusts overall strategy
│   │
│   ├── tools/                   # External service wrappers (mock-first)
│   │   ├── threads_api.py       # Threads publish + metrics (Mock + Real)
│   │   ├── reddit_client.py     # PRAW viral content research
│   │   ├── apify_client.py      # Threads scraping via Apify
│   │   └── embeddings.py        # Novelty scoring via cosine similarity
│   │
│   ├── prompts/                 # All LLM prompt templates
│   ├── store/                   # Knowledge base (LangGraph Store wrapper)
│   ├── orchestrator.py          # APScheduler (cron-like scheduling)
│   └── persistence.py           # Checkpointer + Store factory
│
├── bot/                         # Telegram approval bot
│   ├── telegram_bot.py          # Bot setup + message formatting
│   ├── handlers/                # Approve/Edit/Reject callbacks
│   └── webhook.py               # FastAPI webhook endpoint
│
├── api/                         # FastAPI server
│   └── main.py                  # Health + status + webhook endpoints
│
├── scripts/
│   ├── manual_run.py            # Run a single cycle (interactive or auto)
│   ├── init_account.py          # Initialize niche config in store
│   └── check_health.py          # Verify everything is connected
│
└── tests/                       # 20 tests covering nodes, tools, graph compilation
```

## Knowledge Base

Both pipelines share a persistent knowledge base via [LangGraph Store](https://langchain-ai.github.io/langgraph/concepts/persistence/#store) — a key-value store with namespace separation:

```
┌─────────────────────────────────────────────────┐
│                 LangGraph Store                  │
│                                                  │
│  config/             Account niche & voice       │
│  strategy/           Current content strategy    │
│  pattern_performance/ Which patterns work best   │
│  published_posts/    Full post history           │
│  pending_metrics/    Posts awaiting measurement  │
│  metrics_history/    Engagement data over time   │
│  research_cache/     Cached viral content (24h)  │
└─────────────────────────────────────────────────┘
```

In development: `InMemoryStore`. In production: `AsyncPostgresStore` with embedding support for semantic search.

## Configuring Your Niche

Edit `config/account_niche.yaml` to match your account:

```yaml
niche: "tech"
sub_niche: "programming & startups"

voice:
  tone: "conversational, insightful, slightly provocative"
  persona: "experienced developer who shares hard-won lessons"
  style_notes:
    - "Use short, punchy sentences"
    - "Lead with a controversial or surprising take"
    - "End with a question or call-to-action"

content_pillars:
  - name: "hot_takes"
    description: "Contrarian opinions on tech trends"
    weight: 0.30
  - name: "practical_tips"
    description: "Actionable coding tips and tool recommendations"
    weight: 0.25
  - name: "career_insights"
    description: "Career advice, salary transparency"
    weight: 0.20
  - name: "ai_updates"
    description: "Latest AI/LLM developments explained simply"
    weight: 0.15
  - name: "startup_stories"
    description: "Lessons from building products"
    weight: 0.10

avoid_topics:
  - "political opinions unrelated to tech"
  - "cryptocurrency shilling"
```

The agent uses this config in every generation cycle to stay on-brand and on-topic.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) 0.3+ | Two-graph architecture with shared state |
| LLM | Claude Sonnet 4 via [langchain-anthropic](https://github.com/langchain-ai/langchain) | Pattern extraction, generation, ranking, analysis |
| State Persistence | LangGraph Checkpointer | Survives interrupts, restarts, crashes |
| Knowledge Base | LangGraph Store | Cross-pipeline memory with namespaces |
| Human-in-the-Loop | LangGraph `interrupt()` + [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | Pause graph → Telegram notification → resume on response |
| Research | [PRAW](https://praw.readthedocs.io/) + [Apify](https://apify.com/) | Reddit + Threads viral content discovery |
| Novelty Scoring | Cosine similarity on embeddings | Prevent repetitive content |
| Scheduling | [APScheduler](https://apscheduler.readthedocs.io/) | Creation 3x/day, learning 1x/day |
| API | [FastAPI](https://fastapi.tiangolo.com/) | Webhook receiver + status dashboard |
| Database | PostgreSQL (prod) / In-memory (dev) | Checkpoints, store, metrics |
| Validation | [Pydantic](https://docs.pydantic.dev/) v2 | Structured LLM output + data models |

## Tests

```bash
uv run pytest tests/ -v
```

```
tests/test_graphs/test_creation_pipeline.py::test_creation_pipeline_compiles       PASSED
tests/test_graphs/test_creation_pipeline.py::test_creation_pipeline_has_correct_nodes PASSED
tests/test_graphs/test_learning_pipeline.py::test_learning_pipeline_compiles       PASSED
tests/test_graphs/test_learning_pipeline.py::test_learning_pipeline_has_correct_nodes PASSED
tests/test_nodes/test_goal_check.py::test_goal_not_reached                         PASSED
tests/test_nodes/test_goal_check.py::test_goal_reached                             PASSED
tests/test_nodes/test_publishing.py::test_publish_post                             PASSED
tests/test_nodes/test_publishing.py::test_publish_post_no_selection                PASSED
tests/test_nodes/test_publishing.py::test_schedule_metrics_check                   PASSED
tests/test_nodes/test_research.py::test_research_returns_posts                     PASSED
tests/test_tools/test_embeddings.py::test_cosine_similarity_identical              PASSED
tests/test_tools/test_embeddings.py::test_cosine_similarity_orthogonal             PASSED
tests/test_tools/test_embeddings.py::test_mock_embeddings                          PASSED
tests/test_tools/test_embeddings.py::test_mock_embeddings_deterministic            PASSED
tests/test_tools/test_embeddings.py::test_novelty_score_no_history                 PASSED
tests/test_tools/test_embeddings.py::test_novelty_score_with_history               PASSED
tests/test_tools/test_threads_api.py::test_mock_follower_count                     PASSED
tests/test_tools/test_threads_api.py::test_mock_publish                            PASSED
tests/test_tools/test_threads_api.py::test_mock_metrics                            PASSED
tests/test_tools/test_threads_api.py::test_mock_user_posts                         PASSED

20 passed in 1.07s
```

## Production Deployment

```bash
# Start Postgres
docker compose up -d postgres

# Set production env
export ENV=production
export POSTGRES_URI=postgresql://agent:agent_password@localhost:5432/agent_db

# Or run everything in Docker
docker compose up -d
```

## Roadmap

- [x] Two-graph architecture (creation + learning)
- [x] Mock-first development (works without any API keys except Anthropic)
- [x] Multi-signal ranking (AI + history + novelty)
- [x] Human-in-the-loop via `interrupt()`
- [x] Configurable niche/voice/audience
- [ ] Real Threads API integration (pending API access)
- [ ] Telegram bot approval flow (end-to-end)
- [ ] LangSmith observability dashboard
- [ ] A/B testing (publish two variants, compare)
- [ ] Multi-platform support (X, Bluesky, LinkedIn)
- [ ] Web dashboard for strategy visualization

## Contributing

Contributions welcome! Some good first issues:

- Add more content pattern templates
- Implement real Reddit research with better filtering
- Add rate limiting and retry logic for API calls
- Build a web dashboard showing learning progress
- Add support for image/carousel posts

## License

MIT
