from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from config.settings import Settings

# Free OpenAI-compatible endpoints (bansos router):
#   http://127.0.0.1:17070/v1 — bansos free models
#   http://127.0.0.1:20127/v1 — 9router
# Default for AutoViralAI: bansos free tier.

DEFAULT_FREE_BASE_URL = "http://127.0.0.1:17070/v1"
DEFAULT_FREE_MODEL = "stealth/crouton-alpha"


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

    # openai_free — OpenAI-compatible free models via bansos/9router
    base_url = settings.openai_base_url or DEFAULT_FREE_BASE_URL
    api_key = settings.openai_api_key or "free-key"  # local routers often ignore key
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        max_tokens=8192,
        max_retries=3,
    )
