"""Remediation recommendation ORM model."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.connection import Base
from app.models.enums import RecommendationConfidence, RecommendationSource


def _new_uuid() -> str:
    return str(uuid4())


def _enum(enum_type: type) -> Enum:
    return Enum(
        enum_type,
        values_callable=lambda values: [item.value for item in values],
        native_enum=False,
    )


class RemediationRecommendation(Base):
    """Structured explanation and safe correction attached to a finding."""

    __tablename__ = "remediation_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    cause: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_correction: Mapped[str] = mapped_column(Text, nullable=False)
    safe_example: Mapped[str] = mapped_column(Text, nullable=False)
    generation_source: Mapped[RecommendationSource] = mapped_column(
        _enum(RecommendationSource),
        nullable=False,
    )
    template_id: Mapped[Optional[str]] = mapped_column(String(128))
    confidence: Mapped[RecommendationConfidence] = mapped_column(
        _enum(RecommendationConfidence),
        nullable=False,
    )

    finding: Mapped["Finding"] = relationship(
        "Finding",
        back_populates="remediation",
    )


__all__ = ["RemediationRecommendation"]
