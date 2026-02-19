from pydantic import BaseModel, Field


class ViralPost(BaseModel):
    platform: str = Field(description="Source platform: threads, reddit, x")
    author: str = ""
    content: str
    url: str = ""
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    views: int = 0
    engagement_rate: float = 0.0
    discovered_at: str = ""
    topic_tags: list[str] = Field(default_factory=list)

    @property
    def total_engagement(self) -> int:
        return self.likes + self.replies + self.reposts


class ContentPattern(BaseModel):
    name: str = Field(description="Short pattern name, e.g. 'contrarian_hot_take'")
    description: str = Field(description="What makes this pattern work")
    structure: str = Field(description="Template structure, e.g. 'Hook -> Evidence -> CTA'")
    hook_type: str = Field(description="Type of hook: question, bold_claim, story, stat, etc.")
    example_hooks: list[str] = Field(
        default_factory=list,
        description="2-3 example hooks that use this pattern",
    )
    avg_engagement_rate: float = Field(
        default=0.0,
        description="Average engagement rate of posts using this pattern",
    )
    best_for_pillars: list[str] = Field(
        default_factory=list,
        description="Which content pillars this pattern works best for",
    )
    source_posts_count: int = Field(
        default=0,
        description="How many viral posts exhibited this pattern",
    )
