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
    LanguageCoverageLevel,
    LanguageCoverageRole,
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


class LanguageCoverageProfile(ApiSchema):
    """Declared analysis depth for one supported language."""

    language: str
    role: LanguageCoverageRole
    coverage_level: LanguageCoverageLevel
    supports_data_flow: bool
    supported_rule_ids: list[str]
    limitations: list[str] = Field(default_factory=list)


class LanguageCoverageResult(ApiSchema):
    """Coverage actually applied to one language in an analysis."""

    language: str
    files_seen: int = Field(ge=0)
    files_analyzed: int = Field(ge=0)
    rules_applied: int = Field(ge=0)
    limitations: list[str] = Field(default_factory=list)


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
    language_coverage_profiles: list[LanguageCoverageProfile] = Field(
        default_factory=list,
    )
    language_coverage_results: list[LanguageCoverageResult] = Field(
        default_factory=list,
    )


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
    # AI-suggested re-classification, always a suggestion for a human
    # reviewer to accept via POST /findings/{id}/override -- never applied
    # automatically, and only ever set by a real Ollama classification.
    suggested_severity: Severity | None = None
    severity_rationale: str | None = None


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
    "LanguageCoverageProfile",
    "LanguageCoverageResult",
    "OverrideFindingRequest",
    "PullRequestAnalysis",
    "RemediationRecommendation",
]
