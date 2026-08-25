"""Response schemas for the SecureOps analytics dashboard endpoints.

These are aggregate read-model shapes (counts, week buckets, a pagination
envelope) rather than 1:1 entity mirrors, so they live apart from
app/api/schemas.py, which maps directly onto persisted resources.
"""

from __future__ import annotations

from datetime import date

from pydantic import Field

from app.api.schemas import ApiSchema
from app.models.enums import FindingStatus, Severity


class SeverityDistributionSegment(ApiSchema):
    """One donut segment: a severity bucket or the combined resolved bucket."""

    bucket: str
    count: int = Field(ge=0)


class SeverityDistribution(ApiSchema):
    """Severity distribution response for the dashboard donut widget."""

    repository: str
    segments: list[SeverityDistributionSegment]
    total: int = Field(ge=0)


class WeeklyTrendPoint(ApiSchema):
    """One week's finding count for the trend line widget."""

    week_start: date
    count: int = Field(ge=0)


class WeeklyTrend(ApiSchema):
    """Weekly trend response. Sparse: only weeks with findings are included."""

    repository: str
    points: list[WeeklyTrendPoint]


class TopCriticalFile(ApiSchema):
    """One ranked file for the top-critical-files widget."""

    file_path: str
    count: int = Field(ge=0)
    finding_id: str
    line_start: int = Field(ge=1)


class TopCriticalFiles(ApiSchema):
    """Top critical files response."""

    repository: str
    files: list[TopCriticalFile]


class FindingListItem(ApiSchema):
    """One row of the paginated findings-list widget."""

    id: str
    file_path: str
    line_start: int = Field(ge=1)
    line_end: int | None = None
    rule_id: str
    category: str | None = None
    severity: Severity
    status: FindingStatus
    short_description: str
    fingerprint: str


class FindingListPage(ApiSchema):
    """Paginated findings-list response."""

    items: list[FindingListItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


__all__ = [
    "FindingListItem",
    "FindingListPage",
    "SeverityDistribution",
    "SeverityDistributionSegment",
    "TopCriticalFile",
    "TopCriticalFiles",
    "WeeklyTrend",
    "WeeklyTrendPoint",
]
