import asyncio
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.models.content import RankedPost
from src.models.state import CreationPipelineState
from src.prompts.ranking_prompts import RANK_POSTS_SYSTEM, RANK_POSTS_USER
from src.store.knowledge_base import KnowledgeBase
from src.tools.embeddings import EmbeddingClient, cosine_similarity

logger = logging.getLogger(__name__)

DEFAULT_NOVELTY_SCORE = 8.0
DEFAULT_AI_SCORE = 5.0
DEFAULT_HISTORY_SCORE = 5.0


class AIScoreResult(BaseModel):
    class PostScore(BaseModel):
        index: int = Field(description="0-based index of the variant")
        ai_score: float = Field(ge=0.0, le=10.0)
        reasoning: str

    scores: list[PostScore] = Field(description="Score for each variant")


async def rank_and_select(
    state: CreationPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
    embedding_client: EmbeddingClient | None = None,
) -> dict:
    variants = state.get("generated_variants", [])
    if not variants:
        return {
            "ranked_posts": [],
            "selected_post": None,
            "errors": ["rank_and_select: No variants to rank"],
        }

    niche_config, recent_contents = await asyncio.gather(
        kb.get_niche_config(),
        kb.get_recent_post_contents(limit=20),
    )
    audience_desc = ""
    if niche_config:
        audience_desc = (
            f"Primary: {niche_config.audience.primary}\n"
            f"Secondary: {niche_config.audience.secondary}"
        )

    variants_text = "\n\n".join(
        f"[Variant {i}]\n"
        f"Content: {v.get('content', '')}\n"
        f"Pattern: {v.get('pattern_used', '')}\n"
        f"Pillar: {v.get('pillar', '')}"
        for i, v in enumerate(variants)
    )

    structured_llm = llm.with_structured_output(AIScoreResult)
    try:
        ai_result = await structured_llm.ainvoke(
            [
                SystemMessage(content=RANK_POSTS_SYSTEM),
                HumanMessage(
                    content=RANK_POSTS_USER.format(
                        variants=variants_text,
                        audience_description=audience_desc or "Tech professionals and developers",
                    )
                ),
            ]
        )
    except Exception as e:
        logger.exception("LLM call failed in rank_and_select")
        return {
            "ranked_posts": [],
            "selected_post": None,
            "errors": [f"rank_and_select: LLM call failed: {e}"],
        }

    ai_scores = {s.index: (s.ai_score, s.reasoning) for s in ai_result.scores}

    unique_patterns = list({v.get("pattern_used", "") for v in variants})
    perf_results = await asyncio.gather(*[kb.get_pattern_performance(p) for p in unique_patterns])
    pattern_scores = {
        p: perf.effectiveness_score for p, perf in zip(unique_patterns, perf_results, strict=True)
    }

    if embedding_client is None:
        embedding_client = EmbeddingClient()

    variant_texts = [v.get("content", "") for v in variants]
    all_texts = variant_texts + recent_contents
    all_embeddings = await embedding_client.embed_texts(all_texts) if all_texts else []
    variant_embs = all_embeddings[: len(variant_texts)]
    recent_embs = all_embeddings[len(variant_texts) :]

    ranked = []
    for i, v in enumerate(variants):
        ai_score, reasoning = ai_scores.get(i, (DEFAULT_AI_SCORE, "No score available"))
        history_score = pattern_scores.get(v.get("pattern_used", ""), DEFAULT_HISTORY_SCORE)

        if recent_embs:
            similarities = [cosine_similarity(variant_embs[i], emb) for emb in recent_embs]
            avg_similarity = sum(similarities) / len(similarities)
            novelty = max(0.0, min(10.0, (1 - avg_similarity) * 10))
        else:
            novelty = DEFAULT_NOVELTY_SCORE

        composite = RankedPost.compute_composite(ai_score, history_score, novelty)

        ranked.append(
            RankedPost(
                content=v.get("content", ""),
                pattern_used=v.get("pattern_used", ""),
                pillar=v.get("pillar", ""),
                ai_score=ai_score,
                pattern_history_score=history_score,
                novelty_score=novelty,
                composite_score=composite,
                rank=0,
                reasoning=reasoning,
            )
        )

    ranked.sort(key=lambda r: r.composite_score, reverse=True)
    for i, r in enumerate(ranked):
        r.rank = i + 1

    ranked_dicts = [r.model_dump() for r in ranked]
    selected = ranked_dicts[0] if ranked_dicts else None

    return {
        "ranked_posts": ranked_dicts,
        "selected_post": selected,
    }
