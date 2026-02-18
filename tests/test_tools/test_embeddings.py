"""Tests for embedding utilities."""

import pytest

from src.tools.embeddings import EmbeddingClient, compute_novelty_score, cosine_similarity


def test_cosine_similarity_identical():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_mock_embeddings():
    client = EmbeddingClient()
    embeddings = await client.embed_texts(["hello", "world"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 32  # mock dimension


@pytest.mark.asyncio
async def test_mock_embeddings_deterministic():
    client = EmbeddingClient()
    emb1 = await client.embed_text("test")
    emb2 = await client.embed_text("test")
    assert emb1 == emb2


@pytest.mark.asyncio
async def test_novelty_score_no_history():
    score = await compute_novelty_score("new post", [])
    assert score == 8.0


@pytest.mark.asyncio
async def test_novelty_score_with_history():
    recent = ["programming is fun", "coding tips for beginners"]
    score = await compute_novelty_score("totally different topic about cooking", recent)
    assert 0.0 <= score <= 10.0
