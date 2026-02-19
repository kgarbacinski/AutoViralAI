"""Publishing and metrics models."""

from pydantic import BaseModel, Field


class PublishedPost(BaseModel):
    """A post that has been published to Threads."""

    threads_id: str = Field(description="Threads media container ID")
    content: str
    pattern_used: str
    pillar: str
    published_at: str
    scheduled_metrics_check: str = Field(
        default="",
        description="When to collect metrics (24-48h after publish)",
    )
    follower_count_at_publish: int = 0
    ai_score: float = 0.0
    composite_score: float = 0.0


class PostMetrics(BaseModel):
    """Collected engagement metrics for a published post."""

    threads_id: str
    content: str = ""
    pattern_used: str = ""
    pillar: str = ""
    views: int = 0
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    quotes: int = 0
    engagement_rate: float = 0.0
    follower_delta: int = Field(
        default=0,
        description="Change in followers since post was published",
    )
    collected_at: str = ""
    hours_since_publish: float = 0.0

    @property
    def total_engagement(self) -> int:
        return self.likes + self.replies + self.reposts + self.quotes

    def compute_engagement_rate(self) -> float:
        if self.views == 0:
            return 0.0
        return self.total_engagement / self.views
