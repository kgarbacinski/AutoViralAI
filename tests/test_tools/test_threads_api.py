"""Tests for Threads API mock client."""

import pytest

from src.tools.threads_api import MockThreadsClient


@pytest.mark.asyncio
async def test_mock_follower_count():
    client = MockThreadsClient(initial_followers=50)
    count = await client.get_follower_count()
    assert count >= 50


@pytest.mark.asyncio
async def test_mock_publish():
    client = MockThreadsClient()
    thread_id = await client.publish_post("Hello world")
    assert thread_id.startswith("mock_")


@pytest.mark.asyncio
async def test_mock_metrics():
    client = MockThreadsClient()
    thread_id = await client.publish_post("Test post")
    metrics = await client.get_post_metrics(thread_id)

    assert "views" in metrics
    assert "likes" in metrics
    assert "replies" in metrics
    assert "engagement_rate" in metrics
    assert metrics["views"] > 0


@pytest.mark.asyncio
async def test_mock_user_posts():
    client = MockThreadsClient()
    await client.publish_post("Post 1")
    await client.publish_post("Post 2")

    posts = await client.get_user_posts()
    assert len(posts) == 2
