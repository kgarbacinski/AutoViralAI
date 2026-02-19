from typing import ClassVar

from pydantic import BaseModel, Field


class VoiceConfig(BaseModel):
    tone: str = "conversational, insightful, slightly provocative"
    persona: str = "experienced developer who shares hard-won lessons"
    language: str = "English"
    style_notes: list[str] = Field(default_factory=list)


class AudienceConfig(BaseModel):
    primary: str = "software developers"
    secondary: str = "tech enthusiasts, aspiring founders"
    pain_points: list[str] = Field(default_factory=list)


class ContentPillar(BaseModel):
    name: str
    description: str
    weight: float = Field(ge=0.0, le=1.0)


class AccountNiche(BaseModel):
    niche: str = "tech"
    sub_niche: str = "programming & startups"
    description: str = ""
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    audience: AudienceConfig = Field(default_factory=AudienceConfig)
    content_pillars: list[ContentPillar] = Field(default_factory=list)
    avoid_topics: list[str] = Field(default_factory=list)
    hashtags_primary: list[str] = Field(default_factory=list)
    hashtags_secondary: list[str] = Field(default_factory=list)
    max_hashtags_per_post: int = 3
    posting_timezone: str = "Europe/Warsaw"
    preferred_posting_times: list[str] = Field(default_factory=lambda: ["08:00", "12:30", "18:00"])
    max_posts_per_day: int = 3


class PatternPerformance(BaseModel):
    pattern_name: str
    times_used: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_replies: int = 0
    total_reposts: int = 0
    avg_engagement_rate: float = 0.0
    avg_follower_delta: float = 0.0
    best_post_id: str | None = None
    best_engagement_rate: float | None = None
    worst_post_id: str | None = None
    worst_engagement_rate: float | None = None
    last_used_at: str | None = None

    EXPLORATION_BONUS: ClassVar[float] = 5.0
    ENGAGEMENT_WEIGHT: ClassVar[float] = 0.6
    FOLLOWER_WEIGHT: ClassVar[float] = 0.4
    MAX_SCORE: ClassVar[float] = 10.0

    @property
    def effectiveness_score(self) -> float:
        if self.times_used == 0:
            return self.EXPLORATION_BONUS
        engagement_component = min(self.avg_engagement_rate * 100, self.MAX_SCORE)
        follower_component = min(max(self.avg_follower_delta, 0) * 2, self.MAX_SCORE)
        return (
            self.ENGAGEMENT_WEIGHT * engagement_component
            + self.FOLLOWER_WEIGHT * follower_component
        )


class ContentStrategy(BaseModel):
    preferred_patterns: list[str] = Field(
        default_factory=list,
        description="Pattern names ranked by effectiveness",
    )
    avoid_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns that consistently underperform",
    )
    optimal_posting_times: list[str] = Field(
        default_factory=lambda: ["08:00", "12:30", "18:00"],
    )
    pillar_adjustments: dict[str, float] = Field(
        default_factory=dict,
        description="Adjustments to content pillar weights based on performance",
    )
    key_learnings: list[str] = Field(
        default_factory=list,
        description="Natural language insights from analysis",
    )
    iteration: int = 0
    last_updated: str | None = None
