"""Tests for the human_approval node."""

from unittest.mock import patch

import pytest

from src.nodes.approval import human_approval


@pytest.mark.asyncio
async def test_approval_no_post():
    """No selected_post → reject with error."""
    state = {"selected_post": None, "ranked_posts": []}

    result = await human_approval(state)

    assert result["human_decision"] == "reject"
    assert any("No post selected" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_approval_invalid_type():
    """interrupt returns non-dict → reject with error."""
    state = {
        "selected_post": {"content": "Test post", "pattern_used": "test", "pillar": "tips"},
        "ranked_posts": [],
    }

    with patch("src.nodes.approval.interrupt", return_value="not-a-dict"):
        result = await human_approval(state)

    assert result["human_decision"] == "reject"
    assert any("Invalid decision type" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_approval_invalid_decision():
    """Unknown decision value → defaults to reject."""
    state = {
        "selected_post": {"content": "Test post", "pattern_used": "test", "pillar": "tips"},
        "ranked_posts": [],
    }

    with patch("src.nodes.approval.interrupt", return_value={"decision": "maybe"}):
        result = await human_approval(state)

    assert result["human_decision"] == "reject"
    assert result["selected_post"] is None


@pytest.mark.asyncio
async def test_approval_approve():
    """decision='approve' → selected_post preserved."""
    post = {"content": "Test post", "pattern_used": "test", "pillar": "tips"}
    state = {"selected_post": post, "ranked_posts": []}

    with patch("src.nodes.approval.interrupt", return_value={"decision": "approve"}):
        result = await human_approval(state)

    assert result["human_decision"] == "approve"
    assert result["selected_post"]["content"] == "Test post"


@pytest.mark.asyncio
async def test_approval_edit():
    """decision='edit' with edited_content → content replaced."""
    post = {"content": "Original post", "pattern_used": "test", "pillar": "tips"}
    state = {"selected_post": post, "ranked_posts": []}

    with patch(
        "src.nodes.approval.interrupt",
        return_value={"decision": "edit", "edited_content": "Edited post"},
    ):
        result = await human_approval(state)

    assert result["human_decision"] == "edit"
    assert result["selected_post"]["content"] == "Edited post"
    assert result["human_edited_content"] == "Edited post"


@pytest.mark.asyncio
async def test_approval_reject():
    """decision='reject' → selected_post set to None."""
    post = {"content": "Test post", "pattern_used": "test", "pillar": "tips"}
    state = {"selected_post": post, "ranked_posts": []}

    with patch("src.nodes.approval.interrupt", return_value={"decision": "reject"}):
        result = await human_approval(state)

    assert result["human_decision"] == "reject"
    assert result["selected_post"] is None
