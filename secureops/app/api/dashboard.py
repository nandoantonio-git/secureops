"""Read-only analytics endpoints backing the SecureOps dashboard.

Unlike the write-side persistence in app/api/analyses.py (which is
deliberately fail-soft so the PR-first API keeps working without Postgres),
these endpoints let SQLAlchemyError propagate as a 503
(DependencyUnavailableError). The dashboard needs a real HTTP error to
distinguish "no findings yet" from "the database is down" for its per-widget
retry UI -- a silent empty response would render the wrong empty-state copy.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.api.errors import DependencyUnavailableError
from app.api.dashboard_schemas import (
    FindingListPage,
    SeverityDistribution,
    TopCriticalFiles,
    WeeklyTrend,
)
from app.db.connection import SessionLocal
from app.github.comments import redact_sensitive_feedback
from app.models.enums import FindingStatus, Severity
from app.models.finding import Finding as FindingModel
from app.models.remediation import RemediationRecommendation as RemediationModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_OPEN_STATUSES = (FindingStatus.OPEN, FindingStatus.IN_INVESTIGATION)
_RESOLVED_STATUSES = (FindingStatus.RESOLVED, FindingStatus.ACCEPTED_RISK)
_DONUT_SEVERITIES = (
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
)
_UNAVAILABLE_MESSAGE = "The dashboard data store is unavailable."


@router.get(
    "/severity-distribution",
    response_model=SeverityDistribution,
    operation_id="getSeverityDistribution",
)
def get_severity_distribution(
    repository: str = Query(min_length=1),
) -> dict[str, Any]:
    """Return the 5-bucket severity distribution for a repository.

    Buckets: one per severity (critical/high/medium/low) counting only OPEN
    and IN_INVESTIGATION findings, plus one combined "resolved_accepted"
    bucket for RESOLVED + ACCEPTED_RISK regardless of severity. FALSE_POSITIVE
    findings are excluded entirely -- they are neither an active risk nor a
    resolved-risk decision worth surfacing on an overview screen.
    """

    try:
        with SessionLocal() as session:
            rows = session.execute(
                select(
                    FindingModel.status,
                    FindingModel.severity,
                    func.count(),
                )
                .where(
                    FindingModel.repository == repository,
                    FindingModel.status != FindingStatus.FALSE_POSITIVE,
                )
                .group_by(FindingModel.status, FindingModel.severity),
            ).all()
    except SQLAlchemyError as exc:
        raise DependencyUnavailableError(_UNAVAILABLE_MESSAGE) from exc

    counts_by_status_severity = {
        (status, severity): count for status, severity, count in rows
    }

    segments = []
    for severity in _DONUT_SEVERITIES:
        count = sum(
            n
            for (status, sev), n in counts_by_status_severity.items()
            if sev == severity and status in _OPEN_STATUSES
        )
        segments.append({"bucket": severity.value, "count": count})

    resolved_count = sum(
        n
        for (status, _sev), n in counts_by_status_severity.items()
        if status in _RESOLVED_STATUSES
    )
    segments.append({"bucket": "resolved_accepted", "count": resolved_count})

    total = sum(segment["count"] for segment in segments)
    return {"repository": repository, "segments": segments, "total": total}


@router.get(
    "/weekly-trend",
    response_model=WeeklyTrend,
    operation_id="getWeeklyTrend",
)
def get_weekly_trend(repository: str = Query(min_length=1)) -> dict[str, Any]:
    """Return a sparse weekly finding count trend for a repository.

    Only weeks with at least one finding are returned. The frontend applies
    the "fewer than 2 weeks of data" empty-state rule off the response length.
    """

    week_expr = func.date_trunc("week", FindingModel.created_at)
    try:
        with SessionLocal() as session:
            rows = session.execute(
                select(week_expr.label("week_start"), func.count())
                .where(FindingModel.repository == repository)
                .group_by(week_expr)
                .order_by(week_expr),
            ).all()
    except SQLAlchemyError as exc:
        raise DependencyUnavailableError(_UNAVAILABLE_MESSAGE) from exc

    points = [
        {"week_start": week_start.date(), "count": count}
        for week_start, count in rows
    ]
    return {"repository": repository, "points": points}


@router.get(
    "/top-critical-files",
    response_model=TopCriticalFiles,
    operation_id="getTopCriticalFiles",
)
def get_top_critical_files(
    repository: str = Query(min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    """Return up to `limit` files ranked by open critical findings."""

    critical_open_filters = (
        FindingModel.repository == repository,
        FindingModel.severity == Severity.CRITICAL,
        FindingModel.status.in_(_OPEN_STATUSES),
    )
    try:
        with SessionLocal() as session:
            file_counts = session.execute(
                select(FindingModel.file_path, func.count())
                .where(*critical_open_filters)
                .group_by(FindingModel.file_path)
                .order_by(func.count().desc())
                .limit(limit),
            ).all()

            files = []
            for file_path, count in file_counts:
                latest = session.scalar(
                    select(FindingModel)
                    .where(*critical_open_filters, FindingModel.file_path == file_path)
                    .order_by(FindingModel.created_at.desc())
                    .limit(1),
                )
                files.append(
                    {
                        "file_path": file_path,
                        "count": count,
                        "finding_id": latest.id,
                        "line_start": latest.line_start,
                    },
                )
    except SQLAlchemyError as exc:
        raise DependencyUnavailableError(_UNAVAILABLE_MESSAGE) from exc

    return {"repository": repository, "files": files}


@router.get(
    "/findings",
    response_model=FindingListPage,
    operation_id="listDashboardFindings",
)
def list_dashboard_findings(
    repository: str = Query(min_length=1),
    status: FindingStatus | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Return a page of findings for the findings-list widget, redacted."""

    filters = [FindingModel.repository == repository]
    if status is not None:
        filters.append(FindingModel.status == status)
    if severity is not None:
        filters.append(FindingModel.severity == severity)

    try:
        with SessionLocal() as session:
            total = (
                session.scalar(
                    select(func.count()).select_from(FindingModel).where(*filters),
                )
                or 0
            )

            rows = session.execute(
                select(FindingModel, RemediationModel)
                .join(
                    RemediationModel,
                    RemediationModel.finding_id == FindingModel.id,
                    isouter=True,
                )
                .where(*filters)
                .order_by(FindingModel.created_at.desc())
                .offset(offset)
                .limit(limit),
            ).all()

            items = [
                {
                    "id": finding.id,
                    "file_path": finding.file_path,
                    "line_start": finding.line_start,
                    "line_end": finding.line_end,
                    "rule_id": finding.rule_id,
                    "category": finding.category,
                    "severity": finding.severity,
                    "status": finding.status,
                    "short_description": redact_sensitive_feedback(
                        remediation.cause if remediation is not None else "",
                    ),
                    "fingerprint": finding.fingerprint,
                }
                for finding, remediation in rows
            ]
    except SQLAlchemyError as exc:
        raise DependencyUnavailableError(_UNAVAILABLE_MESSAGE) from exc

    return {"items": items, "total": total, "limit": limit, "offset": offset}


__all__ = ["router"]
