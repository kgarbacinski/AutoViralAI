import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.models.research import ContentPattern
from src.models.state import CreationPipelineState
from src.models.strategy import AccountNiche
from src.prompts.extraction_prompts import EXTRACT_PATTERNS_SYSTEM, EXTRACT_PATTERNS_USER
from src.store.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class PatternExtractionResult(BaseModel):
    patterns: list[ContentPattern] = Field(description="3-5 extracted content patterns")


async def extract_patterns(
    state: CreationPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
) -> dict:
    viral_posts = state.get("viral_posts", [])
    if not viral_posts:
        return {
            "extracted_patterns": [],
            "errors": ["extract_patterns: No viral posts to analyze"],
        }

    niche_config = await kb.get_niche_config()
    niche = niche_config or AccountNiche()
    performances = await kb.get_all_pattern_performances()
    perf_summary = (
        "\n".join(
            f"- {p.pattern_name}: used {p.times_used}x, "
            f"avg engagement {p.avg_engagement_rate:.2%}, "
            f"effectiveness {p.effectiveness_score:.1f}/10"
            for p in performances
        )
        or "No historical data yet."
    )

    posts_text = "\n\n".join(
        f"[{i + 1}] Platform: {p.get('platform', 'unknown')}\n"
        f"Content: {p.get('content', '')}\n"
        f"Engagement: {p.get('likes', 0)} likes, {p.get('replies', 0)} replies, "
        f"{p.get('reposts', 0)} reposts"
        for i, p in enumerate(viral_posts[:15])
    )

    structured_llm = llm.with_structured_output(PatternExtractionResult)

    try:
        result = await structured_llm.ainvoke(
            [
                SystemMessage(content=EXTRACT_PATTERNS_SYSTEM),
                HumanMessage(
                    content=EXTRACT_PATTERNS_USER.format(
                        niche=niche.niche,
                        viral_posts=posts_text,
                        pattern_performance=perf_summary,
                    )
                ),
            ]
        )
    except Exception as e:
        logger.exception("LLM call failed in extract_patterns")
        return {
            "extracted_patterns": [],
            "errors": [f"extract_patterns: LLM call failed: {e}"],
        }

    return {"extracted_patterns": [p.model_dump() for p in result.patterns]}
