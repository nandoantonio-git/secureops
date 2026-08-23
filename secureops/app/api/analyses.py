"""Analysis creation and retrieval endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Path

from app.api.schemas import CreateAnalysisRequest, PullRequestAnalysis
from app.config import get_settings
from app.engine.scan import orchestrate_scan
from app.github.comments import format_pr_feedback
from app.models import analysis as _analysis_models
from app.models import remediation as _remediation_models
from app.models.enums import AnalysisStatus, GateDecisionStatus, GateMode, SignalType
from app.remediation.service import build_remediation_recommendation

del _analysis_models, _remediation_models


router = APIRouter(tags=["analyses"])
AnalysisId = Annotated[str, Path(alias="analysisId")]

_ANALYSES: dict[str, dict[str, Any]] = {}
_FINDINGS_BY_ANALYSIS: dict[str, list[dict[str, Any]]] = {}
_PR_FEEDBACK_BY_ANALYSIS: dict[str, str] = {}


@router.post(
    "/analyses",
    status_code=202,
    response_model=PullRequestAnalysis,
    operation_id="createAnalysis",
)
def create_analysis(request: CreateAnalysisRequest) -> dict[str, Any]:
    """Create an analysis and synchronously scan the supplied changed files."""

    analysis_id = str(uuid4())
    now = _utc_now()
    scan_result = orchestrate_scan(
        analysis_id=analysis_id,
        repository=request.repository,
        changed_files=request.changed_files,
    )
    findings = [
        _serialize_scanned_finding(scanned_finding)
        for scanned_finding in scan_result.scanned_findings
    ]
    analysis = {
        "id": analysis_id,
        "repository": request.repository,
        "pull_request_number": request.pull_request_number,
        "commit_sha": request.commit_sha,
        "trigger": request.trigger,
        "mode": request.mode,
        "status": AnalysisStatus.COMPLETED,
        "findings_count": len(findings),
        "failure_reason": None,
        "started_at": now,
        "completed_at": _utc_now(),
    }

    _ANALYSES[analysis_id] = analysis
    _FINDINGS_BY_ANALYSIS[analysis_id] = findings
    _PR_FEEDBACK_BY_ANALYSIS[analysis_id] = format_pr_feedback(
        findings=findings,
        mode=request.mode,
    )
    return analysis


@router.get(
    "/analyses/{analysisId}",
    response_model=PullRequestAnalysis,
    operation_id="getAnalysis",
)
def get_analysis(analysis_id: AnalysisId) -> dict[str, Any]:
    """Return a previously created in-process analysis."""

    from app.api.errors import ResourceNotFoundError

    try:
        return _ANALYSES[analysis_id]
    except KeyError as exc:
        raise ResourceNotFoundError("Analysis was not found.") from exc


@router.get("/analyses/{analysis_id}/gate-decision")
def get_gate_decision(analysis_id: str) -> dict[str, Any]:
    """Return the current gate decision for an in-process analysis."""

    from app.api.errors import ResourceNotFoundError

    try:
        analysis = _ANALYSES[analysis_id]
    except KeyError as exc:
        raise ResourceNotFoundError("Analysis was not found.") from exc

    mode = analysis["mode"]
    decision = (
        GateDecisionStatus.ADVISORY_ONLY
        if mode == GateMode.ADVISORY
        else GateDecisionStatus.PASSED
    )
    return {
        "analysis_id": analysis_id,
        "mode": mode,
        "decision": decision,
        "reasons": ["Advisory mode does not block merge."],
        "blocking_findings": [],
    }


def list_findings_for_analysis(analysis_id: str) -> list[dict[str, Any]]:
    """Return stored findings for an analysis or raise not found."""

    from app.api.errors import ResourceNotFoundError

    if analysis_id not in _ANALYSES:
        raise ResourceNotFoundError("Analysis was not found.")
    return _FINDINGS_BY_ANALYSIS.get(analysis_id, [])


def get_pr_feedback_for_analysis(analysis_id: str) -> str:
    """Return the generated PR feedback comment for an analysis."""

    from app.api.errors import ResourceNotFoundError

    if analysis_id not in _ANALYSES:
        raise ResourceNotFoundError("Analysis was not found.")
    return _PR_FEEDBACK_BY_ANALYSIS.get(
        analysis_id,
        format_pr_feedback(
            findings=_FINDINGS_BY_ANALYSIS.get(analysis_id, []),
            mode=_ANALYSES[analysis_id]["mode"],
        ),
    )


@router.get("/analyses/{analysisId}/pr-feedback", include_in_schema=False)
def get_analysis_pr_feedback(analysis_id: AnalysisId) -> dict[str, str]:
    """Return the generated Markdown feedback that would be posted to the PR."""

    return {
        "analysis_id": analysis_id,
        "comment": get_pr_feedback_for_analysis(analysis_id),
    }


def _serialize_scanned_finding(scanned_finding: Any) -> dict[str, Any]:
    finding = scanned_finding.finding
    finding.id = str(uuid4())
    recommendation = build_remediation_recommendation(
        finding=finding,
        evidence=scanned_finding.evidence,
        sink=scanned_finding.sink,
        user_input=scanned_finding.user_input,
        settings=get_settings(),
    )
    return {
        "id": finding.id,
        "analysis_id": finding.analysis_id,
        "file_path": finding.file_path,
        "line_start": finding.line_start,
        "line_end": finding.line_end,
        "language": finding.language,
        "rule_id": finding.rule_id,
        "category": finding.category,
        "severity": _api_value(finding.severity),
        "status": _api_value(finding.status),
        "source": _api_value(finding.source),
        "fingerprint": finding.fingerprint,
        "remediation": {
            "cause": recommendation.cause,
            "evidence": recommendation.evidence,
            "impact": recommendation.impact,
            "recommended_correction": recommendation.recommended_correction,
            "safe_example": recommendation.safe_example,
            "generation_source": _api_value(recommendation.generation_source),
            "template_id": recommendation.template_id,
            "confidence": _api_value(recommendation.confidence),
        },
        "detection_signals": [
            {
                "signal_type": SignalType.DETERMINISTIC_RULE.value,
                "deterministic": True,
                "summary": f"Deterministic rule {finding.rule_id} matched.",
            },
        ],
        "history": [],
    }


def _api_value(value: Any) -> Any:
    """Return JSON-facing values for enums while preserving plain scalars."""

    return getattr(value, "value", value)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = ["get_pr_feedback_for_analysis", "list_findings_for_analysis", "router"]
