"""Tests for Phase 3 error handling paths."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.nodes.publishing import publish_post
from src.tools.embeddings import cosine_similarity
from src.tools.threads_api import RealThreadsClient

# ── Helpers ──────────────────────────────────────────────────────────


def _httpx_response(json_data: dict) -> MagicMock:
    """Create a mock httpx.Response (sync json(), sync raise_for_status())."""
    resp = MagicMock()
    resp.json.return_value = json_data
    return resp


# ── _wait_for_container ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wait_for_container_timeout():
    """max_attempts exhausted → TimeoutError."""
    client = RealThreadsClient(access_token="fake", user_id="fake")
    mock_resp = _httpx_response({"status": "IN_PROGRESS"})

    try:
        with (
            patch.object(client._client, "get", AsyncMock(return_value=mock_resp)),
            pytest.raises(TimeoutError, match="did not finish"),
        ):
            await client._wait_for_container("c_123", max_attempts=2, initial_interval=0.01)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_container_error_status():
    """status=ERROR → RuntimeError."""
    client = RealThreadsClient(access_token="fake", user_id="fake")
    mock_resp = _httpx_response({"status": "ERROR", "error_message": "bad media"})

    try:
        with (
            patch.object(client._client, "get", AsyncMock(return_value=mock_resp)),
            pytest.raises(RuntimeError, match="bad media"),
        ):
            await client._wait_for_container("c_123", max_attempts=5, initial_interval=0.01)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_container_success():
    """status=FINISHED → returns normally."""
    client = RealThreadsClient(access_token="fake", user_id="fake")
    mock_resp = _httpx_response({"status": "FINISHED"})

    try:
        with patch.object(client._client, "get", AsyncMock(return_value=mock_resp)):
            await client._wait_for_container("c_123", max_attempts=5, initial_interval=0.01)
    finally:
        await client.close()


# ── publish_post follower fallback ───────────────────────────────────


@pytest.mark.asyncio
async def test_publish_follower_fallback(kb):
    """get_follower_count fails → uses state value."""
    mock_client = AsyncMock()
    mock_client.publish_post.return_value = "t_published_001"
    mock_client.get_follower_count.side_effect = RuntimeError("network error")

    state = {
        "selected_post": {
            "content": "Test post",
            "pattern_used": "test",
            "pillar": "tips",
            "ai_score": 7.0,
            "composite_score": 6.5,
        },
        "current_follower_count": 42,
    }

    result = await publish_post(state, threads_client=mock_client, kb=kb)

    assert result["published_post"] is not None
    assert result["published_post"]["follower_count_at_publish"] == 42


# ── cosine_similarity ────────────────────────────────────────────────


def test_cosine_similarity_length_mismatch():
    """Different lengths → ValueError."""
    with pytest.raises(ValueError, match="Vector length mismatch"):
        cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])
