# Contributing to AutoViralAI

Thanks for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Getting Started

```bash
# Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/AutoViralAI.git
cd AutoViralAI

# Install all dependencies (including dev)
uv sync --dev

# Copy env file
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env (only key needed for dev)

# Run tests to verify setup
uv run pytest
```

### Running Locally

```bash
# Run a single creation cycle (mock APIs, interactive approval)
uv run python scripts/manual_run.py

# Auto-approve mode (skips human approval)
uv run python scripts/manual_run.py --auto-approve

# Run the learning pipeline
uv run python scripts/manual_run.py --pipeline learning

# Health check
uv run python scripts/check_health.py
```

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```

2. **Make your changes** and add tests.

3. **Run checks** before committing:
   ```bash
   # Lint
   uv run ruff check .

   # Format
   uv run ruff format .

   # Tests
   uv run pytest
   ```

4. **Commit** with a clear message:
   ```
   feat: add Twitter platform support
   fix: handle empty research results gracefully
   docs: update configuration examples
   test: add ranking edge case tests
   ```

5. **Push and open a PR** against `main`.

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Line length: 100 characters.
- Target: Python 3.12.
- Type hints are expected on all public functions.
- Use `async/await` for I/O operations.

Ruff handles everything — no need for black, isort, or flake8.

## Project Structure

```
src/
├── models/    # Pydantic data models (state, strategy, content, etc.)
├── graphs/    # LangGraph pipeline definitions
├── nodes/     # Individual pipeline steps (one file per node)
├── tools/     # External service wrappers (mock-first)
├── prompts/   # LLM prompt templates
└── store/     # Knowledge base wrapper
```

Key principles:
- **Mock-first**: Every external service has a mock implementation. Tests should never require API keys.
- **Nodes are pure-ish**: Each node takes state + dependencies, returns state updates. Side effects go through injected clients.
- **Structured LLM output**: Use Pydantic models with `.with_structured_output()` — never parse raw text.

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_nodes/test_ranking.py

# Run specific test
uv run pytest tests/test_nodes/test_ranking.py::test_rank_selects_best -v
```

Tests live in `tests/` and mirror the `src/` structure. If you add a new node or tool, add corresponding tests.

## Good First Issues

Look for issues labeled [`good first issue`](https://github.com/kgarbacinski/AutoViralAI/labels/good%20first%20issue). Some ideas:

- Add more content pattern templates
- Improve error handling with retry logic
- Add tests for uncovered edge cases
- Improve documentation or examples
- Add support for new research sources (HackerNews, ProductHunt)

## Adding a New Platform

The architecture supports multiple platforms. To add one:

1. Create `src/tools/your_platform_client.py` implementing the client interface
2. Add mock + real implementations (see `threads_api.py` for reference)
3. Add tests in `tests/test_tools/`
4. Update `config/settings.py` with new env vars
5. Update `.env.example`

## Questions?

Open an issue or start a discussion. We're happy to help!
