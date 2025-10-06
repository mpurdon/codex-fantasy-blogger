"""Sleeper API client utilities."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import requests

from codex_fantasy_blogger.config import config
from codex_fantasy_blogger.models import PlayerProfile, PlayerTrend
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("sleeper")


class SleeperClient:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    def _get(self, path: str, **params) -> dict:
        url = f"{config.sleeper.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_trending_adds(self, limit: int | None = None) -> List[PlayerTrend]:
        limit = limit or config.sleeper.max_trending
        logger.info("Fetching trending adds from Sleeper (limit=%s)", limit)
        payload = self._get(
            "/players/nfl/trending/add",
            season_type=config.sleeper.season_type,
            limit=limit,
        )
        trends = [PlayerTrend(**item) for item in payload]
        logger.info("Retrieved %s trending players", len(trends))
        return trends

    @lru_cache(maxsize=1)
    def get_player_directory(self) -> Dict[str, dict]:
        logger.info("Downloading Sleeper player directory (may take a moment)...")
        directory = self._get("/players/nfl")
        logger.info("Loaded %s player entries", len(directory))
        return directory

    def _sanitize_profile(self, player_id: str, trend: PlayerTrend) -> Optional[PlayerProfile]:
        directory = self.get_player_directory()
        record = directory.get(player_id)
        if not record:
            logger.warning("No player record found for id=%s", player_id)
            return None
        full_name = record.get("full_name")
        if not full_name:
            logger.debug("Skipping non-player entry for id=%s", player_id)
            return None
        espn_id = record.get("espn_id")
        try:
            espn_id = int(espn_id) if espn_id is not None else None
        except (TypeError, ValueError):
            espn_id = None
        return PlayerProfile(
            player_id=player_id,
            name=full_name,
            position=record.get("position"),
            team=record.get("team") or record.get("team_abbr"),
            espn_id=espn_id,
            trending_count=trend.count,
            injury_status=record.get("injury_status"),
            injury_notes=record.get("injury_notes"),
            depth_chart_order=record.get("depth_chart_order"),
            metadata={
                "age": record.get("age"),
                "height": record.get("height"),
                "weight": record.get("weight"),
                "years_exp": record.get("years_exp"),
                "news_updated": record.get("news_updated"),
            },
        )

    def get_profiles_from_trends(
        self, trends: Iterable[PlayerTrend], limit: int
    ) -> List[PlayerProfile]:
        profiles: List[PlayerProfile] = []
        for trend in trends:
            if len(profiles) >= limit:
                break
            profile = self._sanitize_profile(trend.player_id, trend)
            if profile:
                profiles.append(profile)
        logger.info("Prepared %s player profiles", len(profiles))
        return profiles
