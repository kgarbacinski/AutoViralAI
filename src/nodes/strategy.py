"""Strategy adjustment node - LLM synthesizes updated strategy from learnings."""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.state import LearningPipelineState
from src.models.strategy import ContentStrategy
from src.prompts.strategy_prompts import ADJUST_STRATEGY_SYSTEM, ADJUST_STRATEGY_USER
from src.store.knowledge_base import KnowledgeBase


async def adjust_strategy(
    state: LearningPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
) -> dict:
    """Use LLM to generate an updated content strategy based on performance data."""
    analysis = state.get("performance_analysis")
    if not analysis:
        return {
            "new_strategy": None,
            "errors": ["adjust_strategy: No performance analysis available"],
        }

    current_strategy = await kb.get_strategy()
    all_performances = await kb.get_all_pattern_performances()
    niche_config = await kb.get_niche_config()

    analysis_text = "\n".join(
        f"**{k}**: {', '.join(v) if isinstance(v, list) else v}"
        for k, v in analysis.items()
    )

    strategy_text = current_strategy.model_dump_json(indent=2)

    perf_text = "\n".join(
        f"- {p.pattern_name}: {p.times_used} uses, "
        f"engagement {p.avg_engagement_rate:.2%}, "
        f"follower delta {p.avg_follower_delta:+.1f}, "
        f"effectiveness {p.effectiveness_score:.1f}/10"
        for p in all_performances
    ) or "No pattern data yet."

    niche_text = niche_config.model_dump_json(indent=2) if niche_config else "Not configured."

    structured_llm = llm.with_structured_output(ContentStrategy)

    new_strategy = await structured_llm.ainvoke([
        SystemMessage(content=ADJUST_STRATEGY_SYSTEM),
        HumanMessage(
            content=ADJUST_STRATEGY_USER.format(
                analysis=analysis_text,
                current_strategy=strategy_text,
                all_pattern_performance=perf_text,
                niche_config=niche_text,
            )
        ),
    ])

    new_strategy.iteration = current_strategy.iteration + 1

    await kb.save_strategy(new_strategy)

    return {"new_strategy": new_strategy.model_dump()}
