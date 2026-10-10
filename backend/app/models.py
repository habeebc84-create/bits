"""Persistent schemas with full provenance (no single AI-text blobs)."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    canonical_name: Mapped[str] = mapped_column(String(256))
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    exchange: Mapped[str] = mapped_column(String(16))
    sector: Mapped[str] = mapped_column(String(64))
    industry: Mapped[str] = mapped_column(String(128), default="")
    website: Mapped[str] = mapped_column(String(512), default="")


class Investigation(Base):
    __tablename__ = "investigations"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    company_id: Mapped[str] = mapped_column(String(16), ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(256))
    ticker: Mapped[str] = mapped_column(String(32))
    exchange: Mapped[str] = mapped_column(String(16))
    track: Mapped[str] = mapped_column(String(8))
    period: Mapped[str] = mapped_column(String(32), default="FY2022-FY2025")
    depth: Mapped[str] = mapped_column(String(16), default="standard")
    status: Mapped[str] = mapped_column(String(24), default="queued")  # queued|running|completed|failed|cancelled
    stage: Mapped[str] = mapped_column(String(48), default="queued")
    stage_index: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    retriable: Mapped[int] = mapped_column(Integer, default=0)
    discovery_id: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[str] = mapped_column(String(48), default="")
    events: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of {ts,stage,message,kind}

    company = relationship("Company")
    sources = relationship("Source", back_populates="investigation", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="investigation", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="investigation", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    investigation_id: Mapped[str] = mapped_column(String(16), ForeignKey("investigations.id"), index=True)
    url: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(Text, default="")
    publisher: Mapped[str] = mapped_column(String(256), default="")
    pub_date: Mapped[str] = mapped_column(String(32), default="")
    retrieved_at: Mapped[str] = mapped_column(String(48), default="")
    doc_type: Mapped[str] = mapped_column(String(64), default="article")  # filing|annual_report|results|presentation|transcript|press|industry|news|peer|data
    reporting_period: Mapped[str] = mapped_column(String(64), default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    extraction_status: Mapped[str] = mapped_column(String(24), default="pending")  # pending|ok|failed
    role: Mapped[str] = mapped_column(String(32), default="context")  # supporting|contradictory|context

    investigation = relationship("Investigation", back_populates="sources")


class Evidence(Base):
    __tablename__ = "evidences"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    investigation_id: Mapped[str] = mapped_column(String(16), ForeignKey("investigations.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(16), ForeignKey("sources.id"))
    claim: Mapped[str] = mapped_column(Text)
    passage: Mapped[str] = mapped_column(Text)
    page_section: Mapped[str] = mapped_column(String(256), default="")
    line_item: Mapped[str] = mapped_column(String(256), default="")
    reporting_period: Mapped[str] = mapped_column(String(64), default="")
    units: Mapped[str] = mapped_column(String(64), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    kind: Mapped[str] = mapped_column(String(24), default="fact")  # fact|calculated|interpretation|hypothesis
    validation: Mapped[str] = mapped_column(String(24), default="unreviewed")  # supported|contradicted|unreviewed

    investigation = relationship("Investigation", back_populates="evidences")


class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    investigation_id: Mapped[str] = mapped_column(String(16), ForeignKey("investigations.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    formula_id: Mapped[str] = mapped_column(String(128))
    inputs_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    value: Mapped[float] = mapped_column(Float)
    units: Mapped[str] = mapped_column(String(64), default="")
    period: Mapped[str] = mapped_column(String(64), default="")
    code_version: Mapped[str] = mapped_column(String(16), default="finlib-v1")

    investigation = relationship("Investigation", back_populates="metrics")


class Hypothesis(Base):
    __tablename__ = "hypotheses"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    investigation_id: Mapped[str] = mapped_column(String(16), ForeignKey("investigations.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    mechanism: Mapped[str] = mapped_column(Text, default="")
    supporting_json: Mapped[str] = mapped_column(Text, default="[]")
    contradicting_json: Mapped[str] = mapped_column(Text, default="[]")
    alternatives_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(24), default="candidate")  # candidate|validated|ruled_out|unresolved
    rationale: Mapped[str] = mapped_column(Text, default="")

    investigation = relationship("Investigation", back_populates="hypotheses")


class Discovery(Base):
    __tablename__ = "discoveries"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=_uid)
    investigation_id: Mapped[str] = mapped_column(String(16), ForeignKey("investigations.id"), index=True)
    headline: Mapped[str] = mapped_column(Text)
    finding: Mapped[str] = mapped_column(Text)
    significance_json: Mapped[str] = mapped_column(Text, default="[]")
    key_numbers_json: Mapped[str] = mapped_column(Text, default="[]")
    timeline_json: Mapped[str] = mapped_column(Text, default="[]")
    counterargument_json: Mapped[str] = mapped_column(Text, default="{}")
    falsification_json: Mapped[str] = mapped_column(Text, default="{}")
    strength: Mapped[str] = mapped_column(String(16), default="Weak")
    strength_rationale: Mapped[str] = mapped_column(Text, default="")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    coverage_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(48), default="")
