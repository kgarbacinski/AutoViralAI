"""Content generation and ranking models."""

from typing import Literal

from pydantic import BaseModel, Field


class PostVariant(BaseModel):
    """A generated post variant."""

    content: str = Field(description="The actual post text (max 500 chars for Threads)")
    pattern_used: str = Field(description="Name of the content pattern used")
    pillar: str = Field(description="Content pillar this post belongs to")
    hook_type: str = Field(description="Type of hook used")
    estimated_engagement: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Estimated engagement level",
    )
    reasoning: str = Field(
        default="",
        description="Why this variant should perform well",
    )


class RankedPost(BaseModel):
    """A post variant with multi-signal scoring."""

    content: str
    pattern_used: str
    pillar: str
    ai_score: float = Field(ge=0.0, le=10.0, description="LLM-assessed viral potential")
    pattern_history_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Historical performance of this pattern",
    )
    novelty_score: float = Field(
        ge=0.0,
        le=10.0,
        description="How different from recent posts (semantic)",
    )
    composite_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Weighted composite: 0.4*ai + 0.3*history + 0.3*novelty",
    )
    rank: int = Field(ge=0, description="Rank among variants (1 = best, 0 = unranked)")
    reasoning: str = ""

    @classmethod
    def compute_composite(
        cls, ai_score: float, pattern_history_score: float, novelty_score: float
    ) -> float:
        return 0.4 * ai_score + 0.3 * pattern_history_score + 0.3 * novelty_score
