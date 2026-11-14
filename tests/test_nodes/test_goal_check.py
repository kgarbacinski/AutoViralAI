"""Tests for goal_check node."""

from unittest.mock import patch

import pytest

from src.nodes.goal_check import goal_check
from src.tools.linkedin_api import MockLinkedInClient


@pytest.mark.asyncio
async def test_goal_not_reached():
    client = MockLinkedInClient(initial_followers=10)
    state = {
        "current_follower_count": 0,
        "target_follower_count": 100,
        "goal_reached": False,
    }
    with patch("random.randint", return_value=0):
        result = await goal_check(state, linkedin_client=client)
    assert result["goal_reached"] is False
    assert result["current_follower_count"] == 10


@pytest.mark.asyncio
async def test_goal_reached():
    client = MockLinkedInClient(initial_followers=105)
    state = {
        "current_follower_count": 0,
        "target_follower_count": 100,
        "goal_reached": False,
    }
    with patch("random.randint", return_value=0):
        result = await goal_check(state, linkedin_client=client)
    assert result["goal_reached"] is True
    assert result["current_follower_count"] == 105
