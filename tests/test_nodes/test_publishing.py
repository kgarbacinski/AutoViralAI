"""Tests for publishing node."""

import pytest

from src.nodes.publishing import publish_post, schedule_metrics_check
from src.tools.threads_api import MockThreadsClient


@pytest.mark.asyncio
async def test_publish_post(kb):
    client = MockThreadsClient()
    state = {
        "selected_post": {
            "content": "Test post content",
            "pattern_used": "test_pattern",
            "pillar": "hot_takes",
            "ai_score": 7.0,
            "composite_score": 6.5,
        },
    }

    result = await publish_post(state, threads_client=client, kb=kb)

    assert result["published_post"] is not None
    assert result["published_post"]["content"] == "Test post content"
    assert result["published_post"]["threads_id"].startswith("mock_")


@pytest.mark.asyncio
async def test_publish_post_no_selection(kb):
    client = MockThreadsClient()
    state = {"selected_post": None}

    result = await publish_post(state, threads_client=client, kb=kb)

    assert result["published_post"] is None
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_schedule_metrics_check(kb):
    state = {
        "published_post": {
            "threads_id": "mock_123",
            "content": "Test",
            "pattern_used": "test",
            "pillar": "hot_takes",
            "published_at": "2025-01-01T00:00:00+00:00",
            "scheduled_metrics_check": "2025-01-02T00:00:00+00:00",
            "ai_score": 7.0,
            "composite_score": 6.5,
        },
    }

    await schedule_metrics_check(state, kb=kb)

    pending = await kb.get_pending_metrics_posts()
    assert len(pending) == 1
    assert pending[0].threads_id == "mock_123"
