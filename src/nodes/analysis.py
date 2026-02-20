import asyncio
import logging

import anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from src.models.state import LearningPipelineState
from src.prompts.analysis_prompts import ANALYZE_PERFORMANCE_SYSTEM, ANALYZE_PERFORMANCE_USER
from src.store.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class PerformanceAnalysis(BaseModel):
    top_performers: list[str] = Field(description="What posts worked and why")
    underperformers: list[str] = Field(description="What posts didn't work and why")
    pattern_insights: list[str] = Field(description="Insights about content patterns")
    timing_insights: list[str] = Field(description="Insights about posting timing")
    pillar_analysis: list[str] = Field(description="Insights about content pillars")
    audience_signals: list[str] = Field(description="What the audience responds to")
    recommendations: list[str] = Field(description="3-5 actionable recommendations")


async def analyze_performance(
    state: LearningPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
) -> dict:
    collected = state.get("collected_metrics", [])
    if not collected:
        return {
            "performance_analysis": None,
            "errors": ["analyze_performance: No metrics to analyze"],
        }

    metrics_text = "\n\n".join(
        f"Post: {m.get('content', '')[:200]}\n"
        f"Pattern: {m.get('pattern_used', 'unknown')}\n"
        f"Pillar: {m.get('pillar', 'unknown')}\n"
        f"Views: {m.get('views', 0)}, Likes: {m.get('likes', 0)}, "
        f"Replies: {m.get('replies', 0)}, Reposts: {m.get('reposts', 0)}\n"
        f"Engagement rate: {m.get('engagement_rate', 0):.2%}\n"
        f"Follower delta: {m.get('follower_delta', 0)}"
        for m in collected
    )

    performances, strategy = await asyncio.gather(
        kb.get_all_pattern_performances(),
        kb.get_strategy(),
    )
    perf_text = (
        "\n".join(
            f"- {p.pattern_name}: used {p.times_used}x, "
            f"avg engagement {p.avg_engagement_rate:.2%}, "
            f"effectiveness {p.effectiveness_score:.1f}/10"
            for p in performances
        )
        or "No historical data."
    )
    strategy_text = (
        f"Preferred patterns: {', '.join(strategy.preferred_patterns)}\n"
        f"Key learnings: {'; '.join(strategy.key_learnings)}\n"
        f"Iteration: {strategy.iteration}"
    )

    structured_llm = llm.with_structured_output(PerformanceAnalysis)

    try:
        result = await structured_llm.ainvoke(
            [
                SystemMessage(content=ANALYZE_PERFORMANCE_SYSTEM),
                HumanMessage(
                    content=ANALYZE_PERFORMANCE_USER.format(
                        posts_with_metrics=metrics_text,
                        pattern_performance=perf_text,
                        current_strategy=strategy_text,
                    )
                ),
            ]
        )
    except (anthropic.APIError, OutputParserException, ValidationError) as e:
        logger.exception("LLM call failed in analyze_performance")
        return {
            "performance_analysis": None,
            "errors": [f"analyze_performance: LLM call failed: {e}"],
        }

    return {"performance_analysis": result.model_dump()}
