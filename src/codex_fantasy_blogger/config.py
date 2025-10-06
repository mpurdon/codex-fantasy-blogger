"""Runtime configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class SleeperConfig:
    base_url: str = "https://api.sleeper.app/v1"
    trending_type: str = "add"
    season_type: str = "regular"
    max_trending: int = 40


@dataclass(frozen=True)
class NewsConfig:
    espn_news_url: str = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news"
    google_news_url: str = "https://news.google.com/rss/search"
    max_headlines: int = 3


@dataclass(frozen=True)
class WriterConfig:
    blog_title: str = "Weekly FAAB Watch"
    output_dir: str = "content/posts"
    index_template: str = "blog/index.html.j2"
    post_template: str = "blog/post.md.j2"


@dataclass(frozen=True)
class LLMConfig:
    provider: str = os.environ.get("FAAB_BLOGGER_LLM", "openai")
    model: str = os.environ.get("FAAB_BLOGGER_MODEL", "gpt-4o-mini")
    temperature: float = float(os.environ.get("FAAB_BLOGGER_TEMPERATURE", "0.4"))

    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")


@dataclass(frozen=True)
class AppConfig:
    sleeper: SleeperConfig = SleeperConfig()
    news: NewsConfig = NewsConfig()
    writer: WriterConfig = WriterConfig()
    llm: LLMConfig = LLMConfig()


config = AppConfig()
