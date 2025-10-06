"""LLM helper utilities with graceful degradation."""

from __future__ import annotations

from typing import List, Optional

from codex_fantasy_blogger.config import config
from codex_fantasy_blogger.models import NewsItem, PlayerProfile
from codex_fantasy_blogger.utils.logging import get_logger

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None


logger = get_logger("llm")


class LLMClient:
    def __init__(self) -> None:
        self._client = None
        if OpenAI and config.llm.api_key:
            try:
                self._client = OpenAI(api_key=config.llm.api_key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to initialize OpenAI client: %s", exc)
        else:
            if not OpenAI:
                logger.info("openai package unavailable; falling back to heuristic summaries")
            elif not config.llm.api_key:
                logger.info("OPENAI_API_KEY not set; falling back to heuristic summaries")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _render_headline_bullets(self, headlines: List[NewsItem]) -> str:
        bullets = []
        for item in headlines:
            bullets.append(f"- {item.title} ({item.source})")
        return "\n".join(bullets)

    def draft_blog_section(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        if not self.is_available:
            return fallback
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self._client.responses.create(
                model=config.llm.model,
                temperature=config.llm.temperature,
                input=messages,
            )
            return response.output[0].content[0].text.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM blog section draft failed (%s); using fallback", exc)
            return fallback

    def summarize_context(self, player: PlayerProfile, headlines: List[NewsItem]) -> str:
        if not self.is_available:
            return self._heuristic_summary(player, headlines)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a fantasy football analyst. Summarize why a player is trending on the waiver wire."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Player: {player.name} ({player.position or 'N/A'} - {player.team or 'FA'})\n"
                    f"Trending adds: {player.trending_count}\n"
                    f"Injury status: {player.injury_status or 'None'}\n"
                    f"Headlines:\n{self._render_headline_bullets(headlines)}\n"
                    "Provide a concise summary (2 sentences)."
                ),
            },
        ]
        try:
            response = self._client.responses.create(
                model=config.llm.model,
                temperature=config.llm.temperature,
                input=messages,
            )
            return response.output[0].content[0].text.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM summarization failed for %s (%s); using heuristic fallback",
                player.name,
                exc,
            )
            return self._heuristic_summary(player, headlines)

    def _heuristic_summary(self, player: PlayerProfile, headlines: List[NewsItem]) -> str:
        bullet_text = self._render_headline_bullets(headlines)
        pieces = [
            f"Top notes for {player.name} ({player.team or 'FA'} {player.position or ''}):",
            bullet_text or "- Limited news available; monitor practice reports.",
        ]
        if player.injury_status:
            pieces.append(
                f"Injury status: {player.injury_status}. {player.injury_notes or ''}".strip()
            )
        return "\n".join(pieces).strip()

    def _heuristic_decision(self, player: PlayerProfile, summary: str) -> tuple[str, float, str]:
        rationale_parts = [summary]
        score = min(player.trending_count / 150000, 1.0)
        if player.injury_status and player.injury_status not in {"Questionable", "None", "Healthy"}:
            score *= 0.6
            rationale_parts.append(
                f"Downgraded due to injury status ({player.injury_status})."
            )
        if player.depth_chart_order and player.depth_chart_order > 2:
            score *= 0.7
            rationale_parts.append(
                f"Depth chart order {player.depth_chart_order} lowers upside."
            )
        recommendation = "buy" if score >= 0.5 else "pass"
        confidence = round(score if recommendation == "buy" else 1 - score, 2)
        if recommendation == "pass" and player.trending_count > 90000:
            rationale_parts.append("Could stash in deeper leagues despite recommendation.")
        return recommendation, confidence, " ".join(rationale_parts).strip()

    def evaluate_player(self, player: PlayerProfile, summary: str) -> tuple[str, float, str]:
        if not self.is_available:
            return self._heuristic_decision(player, summary)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert on fantasy football transactions."
                    " Evaluate waiver wire adds, output 'buy' to recommend spending FAAB or 'pass' otherwise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Player: {player.name}\n"
                    f"Position: {player.position}\n"
                    f"Team: {player.team}\n"
                    f"Trending adds: {player.trending_count}\n"
                    f"Injury status: {player.injury_status or 'None'}\n"
                    f"Summary: {summary}\n"
                    "Respond with JSON containing recommendation ('buy' or 'pass'),"
                    " confidence (0-1), and rationale (<=70 words)."
                ),
            },
        ]
        try:
            response = self._client.responses.create(
                model=config.llm.model,
                temperature=config.llm.temperature,
                input=messages,
                response_format={"type": "json_object"},
            )
            payload = response.output[0].content[0].text
            import json

            data = json.loads(payload)
            recommendation = data.get("recommendation", "pass").lower()
            confidence = float(data.get("confidence", 0.5))
            rationale = data.get("rationale", summary)
            return recommendation, confidence, rationale
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse LLM output (%s); using heuristic fallback", exc)
            return self._heuristic_decision(player, summary)
