"""Main orchestration logic for the FAAB blogger pipeline."""

from __future__ import annotations

from pathlib import Path

from codex_fantasy_blogger.agents.player_research_agent import PlayerResearchAgent
from codex_fantasy_blogger.agents.top_adds_agent import TopAddsAgent
from codex_fantasy_blogger.agents.transaction_expert_agent import TransactionExpertAgent
from codex_fantasy_blogger.agents.writer_agent import WriterAgent
from codex_fantasy_blogger.blog.publisher import BlogPublisher
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("orchestrator")


class FaabBlogOrchestrator:
    def __init__(
        self,
        top_adds_agent: TopAddsAgent | None = None,
        research_agent: PlayerResearchAgent | None = None,
        transaction_agent: TransactionExpertAgent | None = None,
        writer_agent: WriterAgent | None = None,
        publisher: BlogPublisher | None = None,
    ) -> None:
        self.top_adds_agent = top_adds_agent or TopAddsAgent()
        self.research_agent = research_agent or PlayerResearchAgent()
        self.transaction_agent = transaction_agent or TransactionExpertAgent()
        self.writer_agent = writer_agent or WriterAgent()
        self.publisher = publisher or BlogPublisher()

    def run(self) -> Path:
        logger.info("Starting FAAB blog generation pipeline")
        profiles = self.top_adds_agent.run()
        logger.info("Researching context for %s players", len(profiles))
        research = self.research_agent.run(profiles)
        evaluations = self.transaction_agent.run(research)
        post = self.writer_agent.run(evaluations)
        output_path = self.publisher.publish(post)
        logger.info("Pipeline completed successfully -> %s", output_path)
        return output_path
