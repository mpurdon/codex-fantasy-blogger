"""CLI entry point for the FAAB blogger pipeline."""

from __future__ import annotations

import typer

from codex_fantasy_blogger.agents.top_adds_agent import TopAddsAgent
from codex_fantasy_blogger.orchestrator import FaabBlogOrchestrator
from codex_fantasy_blogger.utils.logging import get_logger


app = typer.Typer(help="Generate fantasy football FAAB blog posts")
logger = get_logger("cli")


@app.command("generate")
def generate(
    top_n: int = typer.Option(10, help="Number of players to include in the report"),
) -> None:
    """Run the full agentic workflow and publish the post."""
    if top_n <= 0:
        raise typer.BadParameter("top_n must be positive")
    logger.info("Launching FAAB blogger pipeline (top_n=%s)", top_n)
    orchestrator = FaabBlogOrchestrator(top_adds_agent=TopAddsAgent(top_n=top_n))
    post_path = orchestrator.run()
    typer.echo(f"Blog post generated -> {post_path}")


if __name__ == "__main__":
    app()
