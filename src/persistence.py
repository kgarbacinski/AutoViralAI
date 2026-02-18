"""Checkpointer and Store setup for LangGraph."""

from contextlib import asynccontextmanager

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres.aio import AsyncPostgresStore

from config.settings import Settings


def create_checkpointer(settings: Settings):
    """Create an in-memory checkpointer (development only)."""
    return MemorySaver()


def create_store(settings: Settings):
    """Create an in-memory store (development only)."""
    return InMemoryStore()


@asynccontextmanager
async def create_postgres_checkpointer(postgres_uri: str):
    """Create a Postgres checkpointer as an async context manager."""
    async with AsyncPostgresSaver.from_conn_string(postgres_uri) as saver:
        await saver.setup()
        yield saver


@asynccontextmanager
async def create_postgres_store(postgres_uri: str):
    """Create a Postgres store as an async context manager."""
    async with AsyncPostgresStore.from_conn_string(postgres_uri) as store:
        await store.setup()
        yield store
