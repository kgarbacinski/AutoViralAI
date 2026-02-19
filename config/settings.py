"""Application settings using pydantic-settings."""

from pathlib import Path
from typing import Literal

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

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""

    postgres_uri: str = "postgresql://user:password@localhost:5432/agent_db"

    langsmith_api_key: str = ""
    langsmith_project: str = "autoviralai"

    account_id: str = "default"
    target_followers: int = 100
    env: Literal["development", "production"] = "development"

    niche_config_path: Path = CONFIG_DIR / "account_niche.yaml"

    @property
    def is_production(self) -> bool:
        return self.env == "production"


def get_settings() -> Settings:
    return Settings()
