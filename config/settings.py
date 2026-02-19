import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"

    threads_app_id: str = ""
    threads_app_secret: str = ""
    threads_access_token: str = ""
    threads_user_id: str = ""

    apify_api_token: str = ""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "autoviralai/1.0"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""

    postgres_uri: str = ""

    api_secret_key: str = ""

    langsmith_api_key: str = ""
    langsmith_project: str = "autoviralai"

    account_id: str = "default"
    target_followers: int = 100
    env: Literal["development", "production"] = "development"

    niche_config_path: Path = CONFIG_DIR / "account_niche.yaml"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it in .env or as an environment variable."
            )

        if self.is_production:
            missing = []
            if not self.threads_access_token:
                missing.append("THREADS_ACCESS_TOKEN")
            if not self.threads_user_id:
                missing.append("THREADS_USER_ID")
            if not self.postgres_uri:
                missing.append("POSTGRES_URI")
            if not self.api_secret_key:
                logging.getLogger(__name__).warning(
                    "API_SECRET_KEY not set — protected API routes will return 503"
                )
            if not self.telegram_bot_token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if missing:
                raise ValueError(f"Missing required production secrets: {', '.join(missing)}")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
