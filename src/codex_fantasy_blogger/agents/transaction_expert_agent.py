"""Agent that determines buy or pass recommendations."""

from __future__ import annotations

from typing import List

from codex_fantasy_blogger.agents.base import Agent
from codex_fantasy_blogger.models import PlayerEvaluation, PlayerResearch, TransactionDecision
from codex_fantasy_blogger.services.llm import LLMClient
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("agent.transaction")


class TransactionExpertAgent(Agent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("TransactionExpertAgent")
        self.llm = llm or LLMClient()

    def run(self, research_items: List[PlayerResearch]) -> List[PlayerEvaluation]:
        evaluations: List[PlayerEvaluation] = []
        for research in research_items:
            player = research.player
            logger.info("Evaluating transaction stance for %s", player.name)
            recommendation, confidence, rationale = self.llm.evaluate_player(player, research.summary)
            decision = TransactionDecision(
                player=player,
                recommendation=recommendation,
                confidence=confidence,
                rationale=rationale,
            )
            evaluations.append(
                PlayerEvaluation(
                    research=research,
                    decision=decision,
                )
            )
        return evaluations
