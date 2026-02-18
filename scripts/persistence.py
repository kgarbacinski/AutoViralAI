"""Checkpointer and Store setup for LangGraph."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres.aio import AsyncPostgresStore

from config.settings import Settings


def create_checkpointer(settings: Settings):
    """Create the appropriate checkpointer based on environment."""
    if settings.is_production:
        return AsyncPostgresSaver.from_conn_string(settings.postgres_uri)
    return MemorySaver()


def create_store(settings: Settings):
    """Create the appropriate store based on environment."""
    if settings.is_production:
        return AsyncPostgresStore.from_conn_string(settings.postgres_uri)
    return InMemoryStore()
