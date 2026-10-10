"""Typed API schemas with validation."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Track = Literal["A", "B", "C", "D"]
Depth = Literal["quick", "standard", "deep"]


class ResearchCreate(BaseModel):
    company: str = Field(min_length=2, max_length=128)
    exchange: str = Field(default="NSE", max_length=8)
    track: Track = "A"
    period: str = Field(default="FY2022-FY2025", max_length=32)
    depth: Depth = "standard"


class KeyNumber(BaseModel):
    metric: str
    value: float | str
    units: str = ""
    periods: str = ""
    formula: str = ""
    source_ids: list[str] = []


class TimelineItem(BaseModel):
    date: str
    label: str
    kind: str = "signal"


class DiscoveryOut(BaseModel):
    id: str
    investigation_id: str
    headline: str
    finding: str
    significance: list[str]
    key_numbers: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    counterargument: dict[str, Any]
    falsification: dict[str, Any]
    strength: str
    strength_rationale: str
    limitations: list[str]
    coverage: dict[str, Any]
    created_at: str
