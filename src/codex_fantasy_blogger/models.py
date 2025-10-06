"""Shared data models for the FAAB blogger workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlayerTrend(BaseModel):
    player_id: str
    count: int = Field(ge=0)


class PlayerProfile(BaseModel):
    player_id: str
    name: str
    position: Optional[str]
    team: Optional[str]
    espn_id: Optional[int]
    trending_count: int
    injury_status: Optional[str] = None
    injury_notes: Optional[str] = None
    depth_chart_order: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NewsItem(BaseModel):
    source: str
    title: str
    link: str
    published: Optional[datetime] = None
    summary: Optional[str] = None


class PlayerResearch(BaseModel):
    player: PlayerProfile
    headlines: List[NewsItem]
    context_points: List[str]
    summary: str


class TransactionDecision(BaseModel):
    player: PlayerProfile
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class PlayerEvaluation(BaseModel):
    research: PlayerResearch
    decision: TransactionDecision


class BlogPost(BaseModel):
    title: str
    slug: str
    created_at: datetime
    intro: str
    evaluations: List[PlayerEvaluation]
    outro: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "created_at": self.created_at,
            "intro": self.intro,
            "evaluations": [
                {
                    "player": eval.decision.player,
                    "summary": eval.research.summary,
                    "headlines": eval.research.headlines,
                    "context_points": eval.research.context_points,
                    "recommendation": eval.decision.recommendation,
                    "confidence": eval.decision.confidence,
                    "rationale": eval.decision.rationale,
                }
                for eval in self.evaluations
            ],
            "outro": self.outro,
        }
