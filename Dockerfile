FROM python:3.13-slim

WORKDIR /app

# Install uv (pinned version)
COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY . .

# Install the project itself
RUN uv sync --no-dev

# Create non-root user and grant access to app directory
RUN groupadd --system app && useradd --system --gid app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
