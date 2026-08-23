"""Finding listing and detail endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Path

from app.api.analyses import list_findings_for_analysis
from app.api.errors import ResourceNotFoundError
from app.api.schemas import Finding


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

    return find_finding_by_id(finding_id)


def find_finding_by_id(finding_id: str) -> dict[str, Any]:
    """Return a stored finding by id or raise not found."""

    from app.api.analyses import _FINDINGS_BY_ANALYSIS

    for findings in _FINDINGS_BY_ANALYSIS.values():
        for finding in findings:
            if finding["id"] == finding_id:
                return finding
    raise ResourceNotFoundError("Finding was not found.")


__all__ = ["find_finding_by_id", "router"]
