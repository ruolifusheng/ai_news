"""Core data models for Horizon."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class SourceType(str, Enum):
    """Supported information source types."""
    GITHUB = "github"
    HACKERNEWS = "hackernews"
    RSS = "rss"
    TWITTER = "twitter"
    REDDIT = "reddit"


class ContentItem(BaseModel):
    """Unified content item model from any source."""

    id: str  # Format: {source}:{subtype}:{native_id}
    source_type: SourceType
    title: str
    url: HttpUrl
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # AI analysis results
    ai_score: Optional[float] = None  # 0-10 importance score
    ai_reason: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_tags: List[str] = Field(default_factory=list)


class AIProvider(str, Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class AIConfig(BaseModel):
    """AI client configuration."""

    provider: AIProvider
    model: str
    base_url: Optional[str] = None
    api_key_env: str
    temperature: float = 0.3
    max_tokens: int = 4096


class GitHubSourceConfig(BaseModel):
    """GitHub source configuration."""

    type: str  # "user_events", "repo_releases", etc.
    username: Optional[str] = None
    owner: Optional[str] = None
    repo: Optional[str] = None
    enabled: bool = True
    priority: str = "medium"


class HackerNewsConfig(BaseModel):
    """Hacker News configuration."""

    enabled: bool = True
    fetch_top_stories: int = 30
    min_score: int = 100


class RSSSourceConfig(BaseModel):
    """RSS feed source configuration."""

    name: str
    url: HttpUrl
    enabled: bool = True
    category: Optional[str] = None


class TwitterSourceConfig(BaseModel):
    """Twitter source configuration.

    Supports two modes:
    1. Direct RSS URL: Set rss_url to any working Twitter-to-RSS bridge
       (self-hosted RSSHub, whitelisted xcancel, etc.)
    2. Nitter discovery: Tries nitter_instances in order (most are dead in 2024+)
    """

    username: str
    enabled: bool = True
    # Direct RSS URL (preferred - bypasses Nitter instance discovery)
    rss_url: Optional[str] = None
    # Nitter instance URLs as fallback, tried in order
    nitter_instances: List[str] = Field(default_factory=lambda: [
        "https://xcancel.com",
        "https://nitter.poast.org",
    ])


class RedditSubredditConfig(BaseModel):
    """Configuration for monitoring a specific subreddit."""
    subreddit: str
    enabled: bool = True
    sort: str = "hot"           # hot, new, top, rising
    time_filter: str = "day"    # hour, day, week, month, year, all (only for top/controversial)
    fetch_limit: int = 25
    min_score: int = 10


class RedditUserConfig(BaseModel):
    """Configuration for monitoring a specific Reddit user."""
    username: str               # without u/ prefix
    enabled: bool = True
    sort: str = "new"
    fetch_limit: int = 10


class RedditConfig(BaseModel):
    """Reddit source configuration."""
    enabled: bool = True
    subreddits: List[RedditSubredditConfig] = Field(default_factory=list)
    users: List[RedditUserConfig] = Field(default_factory=list)
    fetch_comments: int = 5     # top comments per post, 0 to disable


class SourcesConfig(BaseModel):
    """All sources configuration."""

    github: List[GitHubSourceConfig] = Field(default_factory=list)
    hackernews: HackerNewsConfig = Field(default_factory=HackerNewsConfig)
    rss: List[RSSSourceConfig] = Field(default_factory=list)
    twitter: List[TwitterSourceConfig] = Field(default_factory=list)
    reddit: RedditConfig = Field(default_factory=RedditConfig)


class FilteringConfig(BaseModel):
    """Content filtering configuration."""

    ai_score_threshold: float = 7.0
    time_window_hours: int = 24


class Config(BaseModel):
    """Main configuration model."""

    version: str = "1.0"
    ai: AIConfig
    sources: SourcesConfig
    filtering: FilteringConfig


class SeenItem(BaseModel):
    """Record of a seen content item."""

    first_seen: datetime
    processed: bool = False
    score: Optional[float] = None


class SeenItemsData(BaseModel):
    """Storage for seen items tracking."""

    version: str = "1.0"
    last_run: Optional[datetime] = None
    items: Dict[str, SeenItem] = Field(default_factory=dict)


class SourceRecommendation(BaseModel):
    """Recommended information source."""

    source_type: SourceType
    identifier: str  # username, repo name, RSS URL, etc.
    reason: str
    confidence: float  # 0-1
    sample_content: List[str] = Field(default_factory=list)
