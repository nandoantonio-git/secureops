"""Integration tests for the SecureOps analytics dashboard endpoints.

Dashboard reads query Postgres directly (see app/api/dashboard.py), unlike
the rest of the API which is designed to work without a database. These
tests require a reachable Postgres and skip cleanly when none is available.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api import analyses
from app.db.connection import SessionLocal
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _postgres_available() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="Dashboard endpoint tests require a reachable Postgres database.",
)

_PERSISTED_TABLES = (
    "finding_history_entries",
    "detection_signals",
    "remediation_recommendations",
    "findings",
    "gate_decisions",
    "language_coverage_results",
    "pull_request_analyses",
)


def _reset_database() -> None:
    """Truncate persisted tables so tests don't see state from prior runs."""

    with SessionLocal() as session:
        session.execute(text(f"TRUNCATE {', '.join(_PERSISTED_TABLES)} CASCADE"))
        session.commit()


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for dashboard API checks."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    _reset_database()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
        _reset_database()


def _create_analysis(
    client: TestClient,
    payload: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        "/analyses",
        json={
            "pull_request_number": 1,
            "trigger": "pull_request",
            "mode": "advisory",
            **payload,
        },
    )
    assert response.status_code == 202
    return response.json()


def _critical_finding_payload(repository: str, commit_sha: str) -> dict[str, object]:
    vulnerable_file = (
        FIXTURES_DIR / "python_vulnerable" / "critical_unprotected_data_flow.py"
    )
    second_file = (
        FIXTURES_DIR / "python_vulnerable" / "controlled_critical_unprotected.py"
    )
    return {
        "repository": repository,
        "commit_sha": commit_sha,
        "changed_files": [
            {
                "path": "app/routes/invoices.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
            {
                "path": "app/routes/refunds.py",
                "language": "python",
                "content_ref": str(second_file),
            },
        ],
    }


@pytest.mark.integration
def test_severity_distribution_excludes_false_positive_and_buckets_resolved(
    client: TestClient,
) -> None:
    repository = "secureops/dashboard-severity"
    _create_analysis(client, _critical_finding_payload(repository, "d" * 40))

    findings_response = client.get(
        "/dashboard/findings",
        params={"repository": repository, "limit": 10},
    )
    assert findings_response.status_code == 200
    findings = findings_response.json()["items"]
    assert len(findings) == 2

    # Mark one finding false_positive: it must vanish from the distribution.
    client.post(
        f"/findings/{findings[0]['id']}/override",
        json={
            "changed_by": "reviewer@example.com",
            "change_type": "status_change",
            "to_value": "false_positive",
            "reason": "Confirmed sanitized upstream.",
        },
    )

    response = client.get(
        "/dashboard/severity-distribution",
        params={"repository": repository},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == repository
    buckets = {segment["bucket"]: segment["count"] for segment in body["segments"]}
    assert set(buckets) == {"critical", "high", "medium", "low", "resolved_accepted"}
    # One of the two critical findings was excluded via false_positive.
    assert buckets["critical"] == 1
    assert body["total"] == sum(buckets.values())


@pytest.mark.integration
def test_severity_distribution_empty_for_unknown_repository(
    client: TestClient,
) -> None:
    response = client.get(
        "/dashboard/severity-distribution",
        params={"repository": "secureops/does-not-exist"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert all(segment["count"] == 0 for segment in body["segments"])


@pytest.mark.integration
def test_weekly_trend_has_a_point_for_a_freshly_scanned_repository(
    client: TestClient,
) -> None:
    repository = "secureops/dashboard-trend"
    _create_analysis(client, _critical_finding_payload(repository, "e" * 40))

    response = client.get("/dashboard/weekly-trend", params={"repository": repository})
    assert response.status_code == 200
    points = response.json()["points"]
    assert len(points) == 1
    assert points[0]["count"] == 2


@pytest.mark.integration
def test_top_critical_files_ranks_and_links_findings(client: TestClient) -> None:
    repository = "secureops/dashboard-top-files"
    _create_analysis(client, _critical_finding_payload(repository, "f" * 40))

    response = client.get(
        "/dashboard/top-critical-files",
        params={"repository": repository, "limit": 5},
    )
    assert response.status_code == 200
    files = response.json()["files"]
    assert len(files) == 2
    file_paths = {entry["file_path"] for entry in files}
    assert file_paths == {"app/routes/invoices.py", "app/routes/refunds.py"}
    for entry in files:
        assert entry["count"] == 1
        assert entry["finding_id"]
        assert entry["line_start"] >= 1


@pytest.mark.integration
def test_findings_list_is_redacted_paginated_and_filterable(
    client: TestClient,
) -> None:
    repository = "secureops/dashboard-findings"
    _create_analysis(client, _critical_finding_payload(repository, "0" * 40))

    first_page = client.get(
        "/dashboard/findings",
        params={"repository": repository, "limit": 1, "offset": 0},
    )
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert first_body["total"] == 2
    assert len(first_body["items"]) == 1
    assert first_body["limit"] == 1
    assert first_body["offset"] == 0

    second_page = client.get(
        "/dashboard/findings",
        params={"repository": repository, "limit": 1, "offset": 1},
    )
    assert second_page.status_code == 200
    assert len(second_page.json()["items"]) == 1
    assert (
        first_body["items"][0]["id"] != second_page.json()["items"][0]["id"]
    )

    filtered = client.get(
        "/dashboard/findings",
        params={"repository": repository, "severity": "critical"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 2
    for item in filtered.json()["items"]:
        assert item["severity"] == "critical"
        assert isinstance(item["short_description"], str)
        assert item["short_description"]
