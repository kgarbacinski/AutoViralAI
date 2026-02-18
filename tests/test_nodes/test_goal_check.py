"""Tests for goal_check node."""

import pytest

from src.nodes.goal_check import goal_check
from src.tools.threads_api import MockThreadsClient


@pytest.mark.asyncio
async def test_goal_not_reached():
    client = MockThreadsClient(initial_followers=10)
    state = {
        "current_follower_count": 0,
        "target_follower_count": 100,
        "goal_reached": False,
    }
    result = await goal_check(state, threads_client=client)
    assert result["goal_reached"] is False
    assert result["current_follower_count"] >= 10


@pytest.mark.asyncio
async def test_goal_reached():
    client = MockThreadsClient(initial_followers=105)
    state = {
        "current_follower_count": 0,
        "target_follower_count": 100,
        "goal_reached": False,
    }
    result = await goal_check(state, threads_client=client)
    assert result["goal_reached"] is True
    assert result["current_follower_count"] >= 100
