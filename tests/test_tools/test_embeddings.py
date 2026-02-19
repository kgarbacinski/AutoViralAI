"""Tests for embedding utilities."""

import pytest

from src.tools.embeddings import EmbeddingClient, cosine_similarity


def test_cosine_similarity_identical():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_embeddings():
    client = EmbeddingClient()
    embeddings = await client.embed_texts(["hello", "world"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 32


@pytest.mark.asyncio
async def test_embeddings_deterministic():
    client = EmbeddingClient()
    emb1 = await client.embed_text("test")
    emb2 = await client.embed_text("test")
    assert emb1 == emb2
