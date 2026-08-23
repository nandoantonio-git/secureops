"""Finding, detection signal, and history ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.connection import Base
from app.models.enums import (
    FindingChangeType,
    FindingSource,
    FindingStatus,
    Severity,
    SignalType,
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


class Finding(Base):
    """Vulnerability report tied to a source location and evidence."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("pull_request_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[Optional[int]] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[Severity] = mapped_column(_enum(Severity), nullable=False)
    status: Mapped[FindingStatus] = mapped_column(
        _enum(FindingStatus),
        nullable=False,
        default=FindingStatus.OPEN,
    )
    source: Mapped[FindingSource] = mapped_column(
        _enum(FindingSource),
        nullable=False,
    )
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )

    analysis: Mapped["PullRequestAnalysis"] = relationship(
        "PullRequestAnalysis",
        back_populates="findings",
    )
    remediation: Mapped[Optional["RemediationRecommendation"]] = relationship(
        "RemediationRecommendation",
        back_populates="finding",
        cascade="all, delete-orphan",
        uselist=False,
    )
    detection_signals: Mapped[list["DetectionSignal"]] = relationship(
        "DetectionSignal",
        back_populates="finding",
        cascade="all, delete-orphan",
    )
    history: Mapped[list["FindingHistoryEntry"]] = relationship(
        "FindingHistoryEntry",
        back_populates="finding",
        cascade="all, delete-orphan",
    )


class DetectionSignal(Base):
    """Independent evidence supporting a finding or blocking decision."""

    __tablename__ = "detection_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[SignalType] = mapped_column(_enum(SignalType), nullable=False)
    deterministic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    finding: Mapped[Finding] = relationship(
        "Finding",
        back_populates="detection_signals",
    )


class FindingHistoryEntry(Base):
    """Append-only record of status changes and manual overrides."""

    __tablename__ = "finding_history_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[FindingChangeType] = mapped_column(
        _enum(FindingChangeType),
        nullable=False,
    )
    from_value: Mapped[Optional[str]] = mapped_column(String(255))
    to_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    finding: Mapped[Finding] = relationship("Finding", back_populates="history")


__all__ = [
    "DetectionSignal",
    "Finding",
    "FindingHistoryEntry",
]
