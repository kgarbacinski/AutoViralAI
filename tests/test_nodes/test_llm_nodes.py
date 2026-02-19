"""Tests for all 5 LLM-calling nodes (analyze, extract, generate, rank, strategy)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.content import PostVariant
from src.models.research import ContentPattern
from src.models.strategy import ContentStrategy
from src.nodes.analysis import PerformanceAnalysis, analyze_performance
from src.nodes.generation import GenerationResult, generate_post_variants
from src.nodes.patterns import PatternExtractionResult, extract_patterns
from src.nodes.ranking import AIScoreResult, rank_and_select
from src.nodes.strategy import adjust_strategy

# ── Helpers ──────────────────────────────────────────────────────────


def _mock_llm(return_value):
    """Create a mock LLM that returns a structured output on ainvoke.

    with_structured_output is a sync method, so we use MagicMock for the
    outer object. ainvoke is async, so we use AsyncMock for the structured
    output's ainvoke method.
    """
    mock = MagicMock()
    mock_structured = MagicMock()
    mock.with_structured_output.return_value = mock_structured
    mock_structured.ainvoke = AsyncMock(return_value=return_value)
    return mock


def _mock_llm_failing(error: Exception | None = None):
    """Create a mock LLM whose ainvoke raises."""
    mock = MagicMock()
    mock_structured = MagicMock()
    mock.with_structured_output.return_value = mock_structured
    mock_structured.ainvoke = AsyncMock(side_effect=error or RuntimeError("LLM unavailable"))
    return mock


# ── analyze_performance ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_success(kb, sample_niche):
    await kb.save_niche_config(sample_niche)
    analysis = PerformanceAnalysis(
        top_performers=["post A had great hook"],
        underperformers=["post B was too generic"],
        pattern_insights=["contrarian works"],
        timing_insights=["morning is best"],
        pillar_analysis=["hot_takes top"],
        audience_signals=["devs love controversy"],
        recommendations=["use more questions"],
    )
    llm = _mock_llm(analysis)

    state = {
        "collected_metrics": [
            {
                "content": "Test post",
                "pattern_used": "hot_take",
                "pillar": "tips",
                "views": 100,
                "likes": 10,
                "replies": 2,
                "reposts": 1,
                "engagement_rate": 0.13,
                "follower_delta": 2,
            }
        ],
    }

    result = await analyze_performance(state, llm=llm, kb=kb)

    assert result["performance_analysis"] is not None
    assert result["performance_analysis"]["top_performers"] == ["post A had great hook"]
    llm.with_structured_output.assert_called_once_with(PerformanceAnalysis)


@pytest.mark.asyncio
async def test_analyze_no_metrics(kb):
    state = {"collected_metrics": []}

    result = await analyze_performance(state, llm=AsyncMock(), kb=kb)

    assert result["performance_analysis"] is None
    assert any("No metrics" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_analyze_llm_failure(kb):
    llm = _mock_llm_failing()
    state = {
        "collected_metrics": [
            {
                "content": "x",
                "pattern_used": "p",
                "pillar": "c",
                "views": 1,
                "likes": 0,
                "replies": 0,
                "reposts": 0,
                "engagement_rate": 0,
                "follower_delta": 0,
            }
        ],
    }

    result = await analyze_performance(state, llm=llm, kb=kb)

    assert result["performance_analysis"] is None
    assert any("LLM call failed" in e for e in result["errors"])


# ── extract_patterns ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_success(kb):
    pattern = ContentPattern(
        name="contrarian",
        description="Disagree with popular opinion",
        structure="Hook -> Evidence -> CTA",
        hook_type="bold_claim",
    )
    llm = _mock_llm(PatternExtractionResult(patterns=[pattern]))

    state = {
        "viral_posts": [{"platform": "threads", "content": "Hot take: X is dead", "likes": 500}],
    }

    result = await extract_patterns(state, llm=llm, kb=kb)

    assert len(result["extracted_patterns"]) == 1
    assert result["extracted_patterns"][0]["name"] == "contrarian"


@pytest.mark.asyncio
async def test_extract_no_posts(kb):
    state = {"viral_posts": []}

    result = await extract_patterns(state, llm=AsyncMock(), kb=kb)

    assert result["extracted_patterns"] == []
    assert any("No viral posts" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_extract_llm_failure(kb):
    llm = _mock_llm_failing()
    state = {"viral_posts": [{"platform": "threads", "content": "test", "likes": 10}]}

    result = await extract_patterns(state, llm=llm, kb=kb)

    assert result["extracted_patterns"] == []
    assert any("LLM call failed" in e for e in result["errors"])


# ── generate_post_variants ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_success(kb, sample_niche, sample_strategy):
    await kb.save_niche_config(sample_niche)
    await kb.save_strategy(sample_strategy)
    variant = PostVariant(
        content="5 things devs get wrong about AI",
        pattern_used="numbered_list",
        pillar="practical_tips",
        hook_type="curiosity",
    )
    llm = _mock_llm(GenerationResult(variants=[variant]))

    state = {
        "extracted_patterns": [
            {
                "name": "numbered_list",
                "description": "Numbered tips",
                "structure": "Hook -> List -> CTA",
                "hook_type": "curiosity",
            }
        ],
    }

    result = await generate_post_variants(state, llm=llm, kb=kb)

    assert len(result["generated_variants"]) == 1
    assert result["generated_variants"][0]["content"] == "5 things devs get wrong about AI"


@pytest.mark.asyncio
async def test_generate_no_patterns(kb):
    state = {"extracted_patterns": []}

    result = await generate_post_variants(state, llm=AsyncMock(), kb=kb)

    assert result["generated_variants"] == []
    assert any("No patterns" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_generate_llm_failure(kb, sample_niche):
    await kb.save_niche_config(sample_niche)
    llm = _mock_llm_failing()
    state = {
        "extracted_patterns": [
            {"name": "p", "description": "d", "structure": "s", "hook_type": "h"}
        ],
    }

    result = await generate_post_variants(state, llm=llm, kb=kb)

    assert result["generated_variants"] == []
    assert any("LLM call failed" in e for e in result["errors"])


# ── rank_and_select ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rank_success(kb, embedding_client):
    scores = AIScoreResult(
        scores=[
            AIScoreResult.PostScore(index=0, ai_score=8.0, reasoning="Great hook"),
            AIScoreResult.PostScore(index=1, ai_score=6.0, reasoning="Decent"),
        ]
    )
    llm = _mock_llm(scores)

    state = {
        "generated_variants": [
            {"content": "Post A", "pattern_used": "hot_take", "pillar": "tips"},
            {"content": "Post B", "pattern_used": "list", "pillar": "career"},
        ],
    }

    result = await rank_and_select(state, llm=llm, kb=kb, embedding_client=embedding_client)

    assert len(result["ranked_posts"]) == 2
    assert result["selected_post"] is not None
    # First post should be ranked #1 (higher ai_score)
    assert result["ranked_posts"][0]["rank"] == 1


@pytest.mark.asyncio
async def test_rank_no_variants(kb):
    state = {"generated_variants": []}

    result = await rank_and_select(state, llm=AsyncMock(), kb=kb)

    assert result["ranked_posts"] == []
    assert result["selected_post"] is None
    assert any("No variants" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_rank_llm_failure(kb):
    llm = _mock_llm_failing()
    state = {
        "generated_variants": [
            {"content": "Post A", "pattern_used": "hot_take", "pillar": "tips"},
        ],
    }

    result = await rank_and_select(state, llm=llm, kb=kb)

    assert result["ranked_posts"] == []
    assert result["selected_post"] is None
    assert any("LLM call failed" in e for e in result["errors"])


# ── adjust_strategy ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_success(kb, sample_niche, sample_strategy):
    await kb.save_niche_config(sample_niche)
    await kb.save_strategy(sample_strategy)

    new_strategy = ContentStrategy(
        preferred_patterns=["contrarian_hot_take", "question"],
        key_learnings=["Questions double replies", "Morning posts perform best"],
        iteration=0,  # Will be overwritten by the node
    )
    llm = _mock_llm(new_strategy)

    state = {
        "performance_analysis": {
            "top_performers": ["post A"],
            "underperformers": ["post B"],
            "recommendations": ["try questions"],
        },
    }

    result = await adjust_strategy(state, llm=llm, kb=kb)

    assert result["new_strategy"] is not None
    # iteration should be incremented from current (1) → 2
    assert result["new_strategy"]["iteration"] == 2
    assert "contrarian_hot_take" in result["new_strategy"]["preferred_patterns"]

    # Verify it was saved to KB
    saved = await kb.get_strategy()
    assert saved.iteration == 2


@pytest.mark.asyncio
async def test_strategy_no_analysis(kb):
    state = {"performance_analysis": None}

    result = await adjust_strategy(state, llm=AsyncMock(), kb=kb)

    assert result["new_strategy"] is None
    assert any("No performance analysis" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_strategy_llm_failure(kb, sample_strategy):
    await kb.save_strategy(sample_strategy)
    llm = _mock_llm_failing()

    state = {
        "performance_analysis": {"top_performers": ["x"], "recommendations": ["y"]},
    }

    result = await adjust_strategy(state, llm=llm, kb=kb)

    assert result["new_strategy"] is None
    assert any("LLM call failed" in e for e in result["errors"])
