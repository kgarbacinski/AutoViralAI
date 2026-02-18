"""State schemas for both LangGraph pipelines."""

import operator
from typing import Annotated, Optional, TypedDict


class CreationPipelineState(TypedDict):
    """State for the Content Creation Pipeline (Graph 1)."""

    current_follower_count: int
    target_follower_count: int
    goal_reached: bool

    viral_posts: list[dict]
    extracted_patterns: list[dict]

    generated_variants: list[dict]
    ranked_posts: list[dict]
    selected_post: Optional[dict]

    human_decision: Optional[str]
    human_edited_content: Optional[str]
    human_feedback: Optional[str]

    published_post: Optional[dict]

    cycle_number: int
    errors: Annotated[list[str], operator.add]


class LearningPipelineState(TypedDict):
    """State for the Metrics & Learning Pipeline (Graph 2)."""

    posts_to_check: list[dict]
    collected_metrics: list[dict]

    performance_analysis: Optional[dict]
    pattern_updates: list[dict]

    new_strategy: Optional[dict]

    cycle_number: int
    errors: Annotated[list[str], operator.add]
