"""Tests for the collect_metrics node."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.models.publishing import PublishedPost
from src.nodes.metrics import collect_metrics


def _make_pending_post(
    threads_id: str = "t_001",
    check_offset_hours: float = -1,
) -> PublishedPost:
    """Create a pending post with a scheduled check time relative to now."""
    now = datetime.now(timezone.utc)
    return PublishedPost(
        threads_id=threads_id,
        content="Test post",
        pattern_used="test_pattern",
        pillar="hot_takes",
        published_at=(now - timedelta(hours=25)).isoformat(),
        scheduled_metrics_check=(now + timedelta(hours=check_offset_hours)).isoformat(),
        follower_count_at_publish=100,
    )


@pytest.mark.asyncio
async def test_collect_metrics_ready(kb, mock_threads):
    """Post with past check_time → metrics collected, pending removed."""
    post = _make_pending_post(check_offset_hours=-1)  # 1h in the past
    await kb.add_pending_metrics(post)

    state: dict = {}
    result = await collect_metrics(state, threads_client=mock_threads, kb=kb)

    assert len(result["collected_metrics"]) == 1
    assert result["collected_metrics"][0]["threads_id"] == "t_001"
    assert result["errors"] == []

    # Pending should be removed
    remaining = await kb.get_pending_metrics_posts()
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_collect_metrics_not_ready(kb, mock_threads):
    """Post with future check_time → skipped."""
    post = _make_pending_post(check_offset_hours=2)  # 2h in the future
    await kb.add_pending_metrics(post)

    state: dict = {}
    result = await collect_metrics(state, threads_client=mock_threads, kb=kb)

    assert len(result["collected_metrics"]) == 0

    # Post should still be pending
    remaining = await kb.get_pending_metrics_posts()
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_collect_metrics_empty_pending(kb, mock_threads):
    """No pending posts → empty result."""
    state: dict = {}
    result = await collect_metrics(state, threads_client=mock_threads, kb=kb)

    assert result["collected_metrics"] == []
    assert result["posts_to_check"] == []
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_collect_metrics_api_failure(kb):
    """get_post_metrics raises → error recorded, post not removed."""
    post = _make_pending_post(check_offset_hours=-1)
    await kb.add_pending_metrics(post)

    failing_client = AsyncMock()
    failing_client.get_post_metrics = AsyncMock(side_effect=RuntimeError("API down"))

    state: dict = {}
    result = await collect_metrics(state, threads_client=failing_client, kb=kb)

    assert len(result["collected_metrics"]) == 0
    assert len(result["errors"]) == 1
    assert "API down" in result["errors"][0]

    # Post should still be pending since collection failed
    remaining = await kb.get_pending_metrics_posts()
    assert len(remaining) == 1
