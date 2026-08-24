"""Finding listing and detail endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Path

from app.api.analyses import list_findings_for_analysis
from app.api.errors import InvalidRequestError, ResourceNotFoundError
from app.api.schemas import Finding, OverrideFindingRequest
from app.models.enums import FindingChangeType, FindingStatus, Severity
from app.models.finding import (
    InvalidFindingStatusTransition,
    validate_finding_status_transition,
)


router = APIRouter(tags=["findings"])
AnalysisId = Annotated[str, Path(alias="analysisId")]
FindingId = Annotated[str, Path(alias="findingId")]


@router.get(
    "/analyses/{analysisId}/findings",
    response_model=list[Finding],
    operation_id="listFindings",
)
def list_analysis_findings(analysis_id: AnalysisId) -> list[dict[str, Any]]:
    """List structured findings for an analysis."""

    return list_findings_for_analysis(analysis_id)


@router.get(
    "/findings/{findingId}",
    response_model=Finding,
    operation_id="getFinding",
)
def get_finding(finding_id: FindingId) -> dict[str, Any]:
    """Return one finding by id."""

    return _finding_detail_response(find_finding_by_id(finding_id))


@router.post(
    "/findings/{findingId}/override",
    response_model=Finding,
    operation_id="overrideFinding",
)
def override_finding(
    finding_id: FindingId,
    request: OverrideFindingRequest,
) -> dict[str, Any]:
    """Manually override a finding and append a visible history entry."""

    finding = find_finding_by_id(finding_id)
    apply_manual_override(finding, request)
    return _finding_detail_response(finding)


def find_finding_by_id(finding_id: str) -> dict[str, Any]:
    """Return a stored finding by id or raise not found."""

    from app.api.analyses import _FINDINGS_BY_ANALYSIS

    for findings in _FINDINGS_BY_ANALYSIS.values():
        for finding in findings:
            if finding["id"] == finding_id:
                return finding
    raise ResourceNotFoundError("Finding was not found.")


def apply_manual_override(
    finding: dict[str, Any],
    request: OverrideFindingRequest,
) -> dict[str, Any]:
    """Apply a manual override to a finding while preserving prior history."""

    from_value = _override_from_value(finding, request.change_type)
    _apply_override_value(finding, request)
    finding.setdefault("history", []).append(
        {
            "changed_by": request.changed_by,
            "change_type": _api_value(request.change_type),
            "from_value": from_value,
            "to_value": request.to_value,
            "reason": request.reason,
            "created_at": _utc_now(),
        },
    )
    return finding


def apply_existing_manual_overrides(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Carry forward visible override history for new matching findings."""

    override_by_fingerprint = _latest_overridden_finding_by_fingerprint()
    for finding in findings:
        fingerprint = finding.get("fingerprint")
        overridden_finding = override_by_fingerprint.get(fingerprint)
        if overridden_finding is None:
            continue

        finding["status"] = overridden_finding["status"]
        finding["severity"] = overridden_finding["severity"]
        finding["history"] = [
            dict(history_entry)
            for history_entry in overridden_finding.get("history", [])
        ]
    return findings


def _finding_detail_response(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a finding detail payload with visible history entries included."""

    response = dict(finding)
    response["history"] = [
        _history_entry_response(history_entry)
        for history_entry in finding.get("history", [])
    ]
    return response


def _history_entry_response(history_entry: Any) -> dict[str, Any]:
    if isinstance(history_entry, dict):
        return dict(history_entry)

    return {
        "changed_by": getattr(history_entry, "changed_by", None),
        "change_type": _api_value(getattr(history_entry, "change_type", None)),
        "from_value": getattr(history_entry, "from_value", None),
        "to_value": getattr(history_entry, "to_value", None),
        "reason": getattr(history_entry, "reason", None),
        "created_at": getattr(history_entry, "created_at", None),
    }


def _apply_override_value(
    finding: dict[str, Any],
    request: OverrideFindingRequest,
) -> None:
    if request.change_type == FindingChangeType.SEVERITY_OVERRIDE:
        finding["severity"] = _valid_severity(request.to_value).value
        return

    to_status = _valid_status(request.to_value)
    from_status = _valid_status(str(finding.get("status", "")))
    try:
        validate_finding_status_transition(from_status, to_status)
    except InvalidFindingStatusTransition as exc:
        raise InvalidRequestError(str(exc)) from exc

    finding["status"] = to_status.value


def _override_from_value(
    finding: dict[str, Any],
    change_type: FindingChangeType,
) -> str:
    if change_type == FindingChangeType.SEVERITY_OVERRIDE:
        return str(finding.get("severity", ""))
    return str(finding.get("status", ""))


def _latest_overridden_finding_by_fingerprint() -> dict[Any, dict[str, Any]]:
    from app.api.analyses import _FINDINGS_BY_ANALYSIS

    overridden_findings: dict[Any, dict[str, Any]] = {}
    for findings in _FINDINGS_BY_ANALYSIS.values():
        for finding in findings:
            fingerprint = finding.get("fingerprint")
            if fingerprint and finding.get("history"):
                overridden_findings[fingerprint] = finding
    return overridden_findings


def _valid_status(value: str) -> FindingStatus:
    try:
        return FindingStatus(value)
    except ValueError as exc:
        raise InvalidRequestError("Invalid finding status override.") from exc


def _valid_severity(value: str) -> Severity:
    try:
        return Severity(value)
    except ValueError as exc:
        raise InvalidRequestError("Invalid finding severity override.") from exc


def _api_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "apply_existing_manual_overrides",
    "apply_manual_override",
    "find_finding_by_id",
    "router",
]
