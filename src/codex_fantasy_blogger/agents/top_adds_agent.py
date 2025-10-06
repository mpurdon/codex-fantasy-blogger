"""Agent responsible for surfacing top FAAB adds."""

from __future__ import annotations

from typing import List

from codex_fantasy_blogger.agents.base import Agent
from codex_fantasy_blogger.models import PlayerProfile
from codex_fantasy_blogger.services.sleeper_client import SleeperClient
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("agent.top_adds")


class TopAddsAgent(Agent):
    def __init__(self, sleeper_client: SleeperClient | None = None, top_n: int = 10) -> None:
        super().__init__("TopAddsAgent")
        self.sleeper_client = sleeper_client or SleeperClient()
        self.top_n = top_n

    def run(self) -> List[PlayerProfile]:
        trends = self.sleeper_client.get_trending_adds(limit=self.top_n * 3)
        profiles = self.sleeper_client.get_profiles_from_trends(trends, self.top_n)
        logger.info("Selected top %s players for evaluation", len(profiles))
        return profiles
