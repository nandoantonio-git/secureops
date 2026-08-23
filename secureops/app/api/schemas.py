"""OpenAPI request and response schemas for the SecureOps API."""

from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.enums import (
    AnalysisStatus,
    AnalysisTrigger,
    FindingChangeType,
    FindingSource,
    FindingStatus,
    GateDecisionStatus,
    GateMode,
    RecommendationConfidence,
    RecommendationSource,
    Severity,
    SignalType,
)


class ApiSchema(BaseModel):
    """Base class for API schemas that may be populated from ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class ChangedFile(ApiSchema):
    """Reference to a changed file that should be analyzed."""

    path: str
    language: str
    content_ref: str


class CreateAnalysisRequest(ApiSchema):
    """Request body for creating a pull request analysis."""

    repository: str
    pull_request_number: int | None = Field(default=None, ge=1)
    commit_sha: str
    trigger: AnalysisTrigger
    mode: GateMode = Field(json_schema_extra={"default": GateMode.ADVISORY.value})
    changed_files: list[ChangedFile] = Field(min_length=1)


class PullRequestAnalysis(ApiSchema):
    """Analysis state and summary returned by analysis endpoints."""

    id: str
    repository: str
    pull_request_number: int | None = None
    commit_sha: str
    trigger: AnalysisTrigger
    mode: GateMode
    status: AnalysisStatus
    findings_count: int = Field(ge=0)
    failure_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RemediationRecommendation(ApiSchema):
    """Structured remediation guidance attached to a finding."""

    cause: str
    evidence: str
    impact: str
    recommended_correction: str
    safe_example: str
    generation_source: RecommendationSource
    template_id: str | None = None
    confidence: RecommendationConfidence


class DetectionSignal(ApiSchema):
    """Evidence signal used to support a finding."""

    signal_type: SignalType
    deterministic: bool
    summary: str


class FindingHistoryEntry(ApiSchema):
    """Manual status, severity, or risk assessment history entry."""

    changed_by: str
    change_type: FindingChangeType
    from_value: str | None = None
    to_value: str
    reason: str
    created_at: datetime


class Finding(ApiSchema):
    """Finding detail returned by finding endpoints."""

    id: str
    analysis_id: str
    file_path: str
    line_start: int = Field(ge=1)
    line_end: int | None = Field(default=None, ge=1)
    language: str
    rule_id: str
    category: str | None = None
    severity: Severity
    status: FindingStatus
    source: FindingSource
    fingerprint: str | None = None
    remediation: RemediationRecommendation
    detection_signals: list[DetectionSignal]
    history: list[FindingHistoryEntry] = Field(default_factory=list)


class GateDecision(ApiSchema):
    """Advisory, pass, or block decision for an analysis."""

    analysis_id: str
    mode: GateMode
    decision: GateDecisionStatus
    reasons: list[str]
    blocking_findings: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("blocking_findings", "blocking_finding_ids"),
    )


class OverrideFindingRequest(ApiSchema):
    """Request body for manually overriding finding status or assessment."""

    changed_by: str
    change_type: FindingChangeType
    to_value: str
    reason: str = Field(min_length=1)


__all__ = [
    "ChangedFile",
    "CreateAnalysisRequest",
    "DetectionSignal",
    "Finding",
    "FindingHistoryEntry",
    "GateDecision",
    "OverrideFindingRequest",
    "PullRequestAnalysis",
    "RemediationRecommendation",
]
