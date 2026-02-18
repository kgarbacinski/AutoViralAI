"""Shared test fixtures."""

import pytest
from langgraph.store.memory import InMemoryStore

from config.settings import Settings
from src.models.strategy import (
    AccountNiche,
    AudienceConfig,
    ContentPillar,
    ContentStrategy,
    VoiceConfig,
)
from src.store.knowledge_base import KnowledgeBase
from src.tools.embeddings import EmbeddingClient
from src.tools.threads_api import MockThreadsClient


@pytest.fixture
def settings():
    return Settings(
        anthropic_api_key="test-key",
        account_id="test",
        target_followers=100,
        env="development",
    )


@pytest.fixture
def store():
    return InMemoryStore()


@pytest.fixture
def kb(store):
    return KnowledgeBase(store=store, account_id="test")


@pytest.fixture
def mock_threads():
    return MockThreadsClient(initial_followers=12)


@pytest.fixture
def embedding_client():
    return EmbeddingClient()


@pytest.fixture
def sample_niche():
    return AccountNiche(
        niche="tech",
        sub_niche="programming & startups",
        description="Tech insights for developers",
        voice=VoiceConfig(
            tone="conversational, insightful",
            persona="experienced developer",
            style_notes=["Short, punchy sentences", "Lead with surprising takes"],
        ),
        audience=AudienceConfig(
            primary="software developers",
            secondary="tech enthusiasts",
            pain_points=["information overload", "career growth"],
        ),
        content_pillars=[
            ContentPillar(name="hot_takes", description="Contrarian tech opinions", weight=0.3),
            ContentPillar(name="practical_tips", description="Coding tips and tools", weight=0.25),
            ContentPillar(name="career_insights", description="Career advice", weight=0.2),
            ContentPillar(name="ai_updates", description="AI developments", weight=0.15),
            ContentPillar(name="startup_stories", description="Startup lessons", weight=0.1),
        ],
        avoid_topics=["politics", "crypto shilling"],
    )


@pytest.fixture
def sample_strategy():
    return ContentStrategy(
        preferred_patterns=["contrarian_hot_take", "numbered_list"],
        key_learnings=["Questions at end drive 2x replies"],
        iteration=1,
    )
