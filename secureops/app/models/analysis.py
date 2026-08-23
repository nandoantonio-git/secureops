"""Analysis, gate, language coverage, and validation scenario ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.connection import Base
from app.models.enums import (
    AnalysisStatus,
    AnalysisTrigger,
    ExpectedBlockingOutcome,
    GateDecisionStatus,
    GateMode,
    LanguageCoverageLevel,
    LanguageCoverageRole,
    ValidationCaseType,
)


def _new_uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum(enum_type: type) -> Enum:
    return Enum(
        enum_type,
        values_callable=lambda values: [item.value for item in values],
        native_enum=False,
    )


class PullRequestAnalysis(Base):
    """One scan of a pull request or controlled validation scenario."""

    __tablename__ = "pull_request_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    repository: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pull_request_number: Mapped[Optional[int]] = mapped_column(Integer)
    commit_sha: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    trigger: Mapped[AnalysisTrigger] = mapped_column(
        _enum(AnalysisTrigger),
        nullable=False,
    )
    mode: Mapped[GateMode] = mapped_column(
        _enum(GateMode),
        nullable=False,
        default=GateMode.ADVISORY,
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        _enum(AnalysisStatus),
        nullable=False,
        default=AnalysisStatus.REQUESTED,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    language_coverage_results: Mapped[list["LanguageCoverageResult"]] = relationship(
        "LanguageCoverageResult",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    gate_decisions: Mapped[list["GateDecision"]] = relationship(
        "GateDecision",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class GateDecision(Base):
    """Advisory/pass/block decision produced for an analysis."""

    __tablename__ = "gate_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("pull_request_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[GateMode] = mapped_column(_enum(GateMode), nullable=False)
    decision: Mapped[GateDecisionStatus] = mapped_column(
        _enum(GateDecisionStatus),
        nullable=False,
    )
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    blocking_finding_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    analysis: Mapped[PullRequestAnalysis] = relationship(
        "PullRequestAnalysis",
        back_populates="gate_decisions",
    )


class LanguageCoverageProfile(Base):
    """Declared support level for a language."""

    __tablename__ = "language_coverage_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    language: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    role: Mapped[LanguageCoverageRole] = mapped_column(
        _enum(LanguageCoverageRole),
        nullable=False,
    )
    coverage_level: Mapped[LanguageCoverageLevel] = mapped_column(
        _enum(LanguageCoverageLevel),
        nullable=False,
    )
    supports_data_flow: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    supported_rule_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class LanguageCoverageResult(Base):
    """Per-analysis language coverage result."""

    __tablename__ = "language_coverage_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("pull_request_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(64), nullable=False)
    files_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    analysis: Mapped[PullRequestAnalysis] = relationship(
        "PullRequestAnalysis",
        back_populates="language_coverage_results",
    )


class ValidationScenario(Base):
    """Controlled fixture case with expected analysis behavior."""

    __tablename__ = "validation_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    language: Mapped[str] = mapped_column(String(64), nullable=False)
    case_type: Mapped[ValidationCaseType] = mapped_column(
        _enum(ValidationCaseType),
        nullable=False,
    )
    expected_findings: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    expected_blocking_outcome: Mapped[ExpectedBlockingOutcome] = mapped_column(
        _enum(ExpectedBlockingOutcome),
        nullable=False,
    )
    reviewer_usefulness_rating: Mapped[Optional[int]] = mapped_column(Integer)


__all__ = [
    "GateDecision",
    "LanguageCoverageProfile",
    "LanguageCoverageResult",
    "PullRequestAnalysis",
    "ValidationScenario",
]
