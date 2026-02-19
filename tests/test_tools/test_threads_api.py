"""Tests for Threads API mock client."""

from unittest.mock import patch

import pytest

from src.tools.threads_api import MockThreadsClient


@pytest.mark.asyncio
async def test_mock_follower_count():
    client = MockThreadsClient(initial_followers=50)
    with patch("random.randint", return_value=2):
        count = await client.get_follower_count()
    assert count == 52


@pytest.mark.asyncio
async def test_mock_publish():
    client = MockThreadsClient()
    thread_id = await client.publish_post("Hello world")
    assert thread_id.startswith("mock_")


@pytest.mark.asyncio
async def test_mock_metrics():
    client = MockThreadsClient()
    thread_id = await client.publish_post("Test post")

    with patch("random.randint", return_value=500), patch("random.uniform", return_value=0.1):
        metrics = await client.get_post_metrics(thread_id)

    assert "views" in metrics
    assert "likes" in metrics
    assert "replies" in metrics
    assert "engagement_rate" in metrics
    assert metrics["views"] == 500


@pytest.mark.asyncio
async def test_mock_user_posts():
    client = MockThreadsClient()
    await client.publish_post("Post 1")
    await client.publish_post("Post 2")

    posts = await client.get_user_posts()
    assert len(posts) == 2
