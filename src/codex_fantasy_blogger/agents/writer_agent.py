"""Agent that assembles the final blog narrative."""

from __future__ import annotations

from datetime import datetime
from typing import List

from codex_fantasy_blogger.agents.base import Agent
from codex_fantasy_blogger.models import BlogPost, PlayerEvaluation
from codex_fantasy_blogger.services.llm import LLMClient
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("agent.writer")


class WriterAgent(Agent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("WriterAgent")
        self.llm = llm or LLMClient()

    def _build_intro(self, evaluations: List[PlayerEvaluation], date_str: str) -> str:
        top_players = ", ".join(eval.decision.player.name for eval in evaluations[:5])
        if not top_players:
            top_players = "waiver-wire targets"
        fallback = (
            f"FAAB season rolls on heading into {date_str}."
            f" Managers are flocking to {top_players} in most leagues right now."
        )
        return self.llm.draft_blog_section(
            system_prompt="You are a fantasy football writer with a conversational tone.",
            user_prompt=(
                "Write an energetic 2-3 sentence introduction for a blog post summarizing"
                " this week's FAAB pickups. Mention the date and at least two of the key"
                f" players: {top_players}. Date: {date_str}."
            ),
            fallback=fallback,
        )

    def _build_outro(self) -> str:
        fallback = (
            "As always, tailor your bids to league depth and roster needs."
            " We'll revisit these moves in next week's FAAB report."
        )
        return self.llm.draft_blog_section(
            system_prompt="You are a seasoned fantasy football analyst.",
            user_prompt=(
                "Write a short closing paragraph (2 sentences) reminding readers to stay flexible"
                " with their FAAB bids and teasing next week's update."
            ),
            fallback=fallback,
        )

    def run(self, evaluations: List[PlayerEvaluation]) -> BlogPost:
        now = datetime.utcnow()
        date_str = now.strftime("%B %d, %Y")
        slug = now.strftime("faab-top-adds-%Y-%m-%d").lower()
        title = f"FAAB Top Adds for {date_str}"
        intro = self._build_intro(evaluations, date_str)
        outro = self._build_outro()
        logger.info("Writer agent produced blog post '%s'", title)
        return BlogPost(
            title=title,
            slug=slug,
            created_at=now,
            intro=intro,
            evaluations=evaluations,
            outro=outro,
        )
