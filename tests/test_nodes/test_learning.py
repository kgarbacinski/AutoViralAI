"""Tests for the update_knowledge_base learning node."""

import pytest

from src.nodes.learning import update_knowledge_base


@pytest.mark.asyncio
async def test_update_kb_single_metric(kb):
    """One metric → pattern perf created, times_used=1, correct engagement rate."""
    state = {
        "collected_metrics": [
            {
                "threads_id": "t_001",
                "pattern_used": "hot_take",
                "views": 1000,
                "likes": 50,
                "replies": 10,
                "reposts": 5,
                "engagement_rate": 0.065,
                "follower_delta": 3,
            }
        ],
    }

    result = await update_knowledge_base(state, kb=kb)

    assert len(result["pattern_updates"]) == 1
    perf = result["pattern_updates"][0]
    assert perf["pattern_name"] == "hot_take"
    assert perf["times_used"] == 1
    assert perf["total_views"] == 1000
    assert perf["total_likes"] == 50
    assert perf["total_replies"] == 10
    assert perf["total_reposts"] == 5
    # engagement rate = (50+10+5) / 1000 = 0.065
    assert perf["avg_engagement_rate"] == pytest.approx(0.065)
    assert perf["avg_follower_delta"] == pytest.approx(3.0)
    assert perf["best_post_id"] == "t_001"
    assert perf["best_engagement_rate"] == pytest.approx(0.065)
    assert perf["worst_post_id"] == "t_001"
    assert perf["worst_engagement_rate"] == pytest.approx(0.065)


@pytest.mark.asyncio
async def test_update_kb_multiple_metrics(kb):
    """Two metrics for same pattern → cumulative stats."""
    state = {
        "collected_metrics": [
            {
                "threads_id": "t_001",
                "pattern_used": "list_post",
                "views": 500,
                "likes": 25,
                "replies": 5,
                "reposts": 5,
                "engagement_rate": 0.07,
                "follower_delta": 2,
            },
            {
                "threads_id": "t_002",
                "pattern_used": "list_post",
                "views": 1000,
                "likes": 60,
                "replies": 20,
                "reposts": 10,
                "engagement_rate": 0.09,
                "follower_delta": 4,
            },
        ],
    }

    result = await update_knowledge_base(state, kb=kb)

    assert len(result["pattern_updates"]) == 2
    final_perf = result["pattern_updates"][1]
    assert final_perf["times_used"] == 2
    assert final_perf["total_views"] == 1500
    assert final_perf["total_likes"] == 85
    # engagement rate = (85+25+15) / 1500 = 0.0833...
    assert final_perf["avg_engagement_rate"] == pytest.approx((85 + 25 + 15) / 1500)
    assert final_perf["avg_follower_delta"] == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_update_kb_best_worst_tracking(kb):
    """Verify best/worst post tracked by actual engagement rate."""
    state = {
        "collected_metrics": [
            {
                "threads_id": "t_high",
                "pattern_used": "question",
                "views": 100,
                "likes": 10,
                "replies": 5,
                "reposts": 0,
                "engagement_rate": 0.15,
                "follower_delta": 1,
            },
            {
                "threads_id": "t_low",
                "pattern_used": "question",
                "views": 200,
                "likes": 2,
                "replies": 0,
                "reposts": 0,
                "engagement_rate": 0.01,
                "follower_delta": 0,
            },
        ],
    }

    result = await update_knowledge_base(state, kb=kb)

    final_perf = result["pattern_updates"][1]
    assert final_perf["best_post_id"] == "t_high"
    assert final_perf["best_engagement_rate"] == pytest.approx(0.15)
    assert final_perf["worst_post_id"] == "t_low"
    assert final_perf["worst_engagement_rate"] == pytest.approx(0.01)


@pytest.mark.asyncio
async def test_update_kb_empty_metrics(kb):
    """Empty collected_metrics → returns empty pattern_updates."""
    state = {"collected_metrics": []}

    result = await update_knowledge_base(state, kb=kb)

    assert result["pattern_updates"] == []


@pytest.mark.asyncio
async def test_update_kb_skips_empty_pattern(kb):
    """Metric with empty pattern_used → skipped."""
    state = {
        "collected_metrics": [
            {
                "threads_id": "t_001",
                "pattern_used": "",
                "views": 100,
                "likes": 5,
                "replies": 1,
                "reposts": 0,
                "engagement_rate": 0.06,
                "follower_delta": 0,
            }
        ],
    }

    result = await update_knowledge_base(state, kb=kb)

    assert result["pattern_updates"] == []
