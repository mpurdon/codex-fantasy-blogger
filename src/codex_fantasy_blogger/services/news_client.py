"""News aggregation utilities."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import feedparser
import requests

from codex_fantasy_blogger.config import config
from codex_fantasy_blogger.models import NewsItem, PlayerProfile
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("news")


class NewsClient:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    def _fetch_espn_headlines(self, espn_id: int) -> List[NewsItem]:
        params = {"athlete": espn_id}
        resp = self.session.get(config.news.espn_news_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items: List[NewsItem] = []
        for article in data.get("articles", [])[: config.news.max_headlines]:
            published = article.get("published") or article.get("lastModified")
            published_dt = None
            if published:
                try:
                    published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                except ValueError:
                    published_dt = None
            summary = article.get("description") or article.get("headline")
            link = article.get("links", {}).get("web", {}).get("href") or ""
            items.append(
                NewsItem(
                    source="ESPN",
                    title=article.get("headline", ""),
                    link=link,
                    published=published_dt,
                    summary=summary,
                )
            )
        return items

    def _fetch_google_news(self, query: str) -> List[NewsItem]:
        params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        url = config.news.google_news_url
        logger.debug("Querying Google News RSS for %s", query)
        feed = feedparser.parse(self.session.get(url, params=params, timeout=10).text)
        items: List[NewsItem] = []
        for entry in feed.entries[: config.news.max_headlines]:
            published_dt = None
            published = entry.get("published")
            if published:
                try:
                    published_dt = datetime(*entry.published_parsed[:6])
                except Exception:  # noqa: BLE001
                    published_dt = None
            summary = entry.get("summary") or entry.get("title")
            items.append(
                NewsItem(
                    source=entry.get("source", {}).get("title", "Google News"),
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    published=published_dt,
                    summary=summary,
                )
            )
        return items

    def get_news_for_player(self, profile: PlayerProfile) -> List[NewsItem]:
        if profile.espn_id:
            try:
                headlines = self._fetch_espn_headlines(profile.espn_id)
                if headlines:
                    return headlines
            except requests.HTTPError as exc:  # fallback on HTTP issues
                logger.warning("ESPN headlines failed for %s (%s)", profile.name, exc)
            except requests.RequestException as exc:
                logger.warning("ESPN request failed for %s (%s)", profile.name, exc)
        query_parts = [profile.name]
        if profile.team:
            query_parts.append(profile.team)
        if profile.position:
            query_parts.append(profile.position)
        query = " ".join(query_parts)
        return self._fetch_google_news(query)
