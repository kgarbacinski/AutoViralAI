"""State schemas for both LangGraph pipelines."""

import operator
from typing import Annotated, TypedDict


class CreationPipelineState(TypedDict):
    """State for the Content Creation Pipeline (Graph 1)."""

    current_follower_count: int
    target_follower_count: int
    goal_reached: bool

    viral_posts: list[dict]
    extracted_patterns: list[dict]

    generated_variants: list[dict]
    ranked_posts: list[dict]
    selected_post: dict | None

    human_decision: str | None
    human_edited_content: str | None
    human_feedback: str | None

    published_post: dict | None

    cycle_number: int
    errors: Annotated[list[str], operator.add]


class LearningPipelineState(TypedDict):
    """State for the Metrics & Learning Pipeline (Graph 2)."""

    posts_to_check: list[dict]
    collected_metrics: list[dict]

    performance_analysis: dict | None
    pattern_updates: list[dict]

    new_strategy: dict | None

    cycle_number: int
    errors: Annotated[list[str], operator.add]
