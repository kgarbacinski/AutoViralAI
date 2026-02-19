import asyncio
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.models.content import PostVariant
from src.models.state import CreationPipelineState
from src.models.strategy import AccountNiche
from src.prompts.generation_prompts import GENERATE_VARIANTS_SYSTEM, GENERATE_VARIANTS_USER
from src.store.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class GenerationResult(BaseModel):
    variants: list[PostVariant] = Field(description="Exactly 5 post variants")


async def generate_post_variants(
    state: CreationPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
) -> dict:
    patterns = state.get("extracted_patterns", [])
    if not patterns:
        return {
            "generated_variants": [],
            "errors": ["generate_post_variants: No patterns available"],
        }

    niche_config, strategy, recent_posts = await asyncio.gather(
        kb.get_niche_config(),
        kb.get_strategy(),
        kb.get_recent_posts(limit=10),
    )
    niche = niche_config or AccountNiche()

    patterns_text = "\n\n".join(
        f"Pattern: {p.get('name', 'unnamed')}\n"
        f"Description: {p.get('description', '')}\n"
        f"Structure: {p.get('structure', '')}\n"
        f"Hook type: {p.get('hook_type', '')}"
        for p in patterns
    )

    pillars_text = "No specific pillars configured."
    if niche.content_pillars:
        pillars_text = "\n".join(
            f"- {p.name} ({p.weight:.0%}): {p.description}" for p in niche.content_pillars
        )

    recent_text = (
        "\n".join(f"- {p.content[:100]}..." for p in recent_posts) or "No posts published yet."
    )

    avoid_text = ", ".join(niche.avoid_topics) if niche.avoid_topics else "None specified."

    strategy_text = (
        "\n".join(strategy.key_learnings)
        if strategy.key_learnings
        else "No learnings yet - first cycle."
    )

    structured_llm = llm.with_structured_output(GenerationResult)

    try:
        result = await structured_llm.ainvoke(
            [
                SystemMessage(content=GENERATE_VARIANTS_SYSTEM.format(niche=niche.niche)),
                HumanMessage(
                    content=GENERATE_VARIANTS_USER.format(
                        niche=niche.niche,
                        voice_tone=niche.voice.tone,
                        voice_persona=niche.voice.persona,
                        style_notes="\n".join(niche.voice.style_notes),
                        patterns=patterns_text,
                        pillars=pillars_text,
                        avoid_topics=avoid_text,
                        recent_posts=recent_text,
                        strategy_learnings=strategy_text,
                    )
                ),
            ]
        )
    except Exception as e:
        logger.exception("LLM call failed in generate_post_variants")
        return {
            "generated_variants": [],
            "errors": [f"generate_post_variants: LLM call failed: {e}"],
        }

    return {"generated_variants": [v.model_dump() for v in result.variants]}
