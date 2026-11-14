from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from config.settings import Settings

# Free OpenAI-compatible endpoints (bansos router):
#   http://127.0.0.1:17070/v1 — bansos free models
#   https://openrouter.ai/api/v1 — OpenRouter free router
# Default for AutoViralAI: OpenRouter's unified free tier.

DEFAULT_FREE_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_FREE_MODEL = "openrouter/free"


def get_llm(settings: Settings):
    provider = settings.llm_provider or "openai_free"
    model = settings.llm_model or DEFAULT_FREE_MODEL

    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            api_key=settings.anthropic_api_key,
            max_tokens=4096,
            max_retries=8,
        )

    base_url = settings.openai_base_url or DEFAULT_FREE_BASE_URL
    api_key = settings.openai_api_key or os.getenv("OPENROUTER_API_KEY", "")

    if not api_key and settings.openrouter_api_key_file:
        key_file = Path(settings.openrouter_api_key_file)
        if key_file.is_file():
            for line in key_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        # Bansos and similar local routers often accept any key.
        api_key = "free-key"

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        max_tokens=32768,
        max_retries=3,
    )
