"""Agent to gather context for each trending player."""

from __future__ import annotations

from typing import List

from codex_fantasy_blogger.agents.base import Agent
from codex_fantasy_blogger.models import PlayerProfile, PlayerResearch
from codex_fantasy_blogger.services.llm import LLMClient
from codex_fantasy_blogger.services.news_client import NewsClient
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("agent.research")


class PlayerResearchAgent(Agent):
    def __init__(self, news_client: NewsClient | None = None, llm: LLMClient | None = None) -> None:
        super().__init__("PlayerResearchAgent")
        self.news_client = news_client or NewsClient()
        self.llm = llm or LLMClient()

    def _build_context_points(self, profile: PlayerProfile) -> List[str]:
        points = [
            f"Trending adds this week: {profile.trending_count:,}",
        ]
        if profile.injury_status:
            status_note = profile.injury_notes or "Monitor practice participation."
            points.append(f"Injury status: {profile.injury_status} — {status_note}")
        if profile.depth_chart_order:
            points.append(f"Depth chart order: {profile.depth_chart_order}")
        years_exp = profile.metadata.get("years_exp")
        if years_exp is not None:
            points.append(f"Years of NFL experience: {years_exp}")
        return points

    def run(self, profiles: List[PlayerProfile]) -> List[PlayerResearch]:
        results: List[PlayerResearch] = []
        for profile in profiles:
            logger.info("Collecting headlines for %s", profile.name)
            headlines = self.news_client.get_news_for_player(profile)
            summary = self.llm.summarize_context(profile, headlines)
            research = PlayerResearch(
                player=profile,
                headlines=headlines,
                context_points=self._build_context_points(profile),
                summary=summary,
            )
            results.append(research)
        return results
