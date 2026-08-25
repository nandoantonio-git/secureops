"""Integration tests for Postgres-backed finding persistence.

These tests require a reachable Postgres (unlike the rest of the suite, which
is designed to pass without one -- see app/api/analyses.py's fail-soft
persistence). They skip cleanly when no database is reachable so the default
local/CI run is unaffected, and run for real wherever Postgres is available.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.api import analyses
from app.db.connection import SessionLocal
from app.main import app
from app.models.finding import Finding as FindingModel


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
    reason="Finding persistence tests require a reachable Postgres database.",
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
    """Truncate persisted tables so tests don't see state from prior runs.

    The in-process cache is cleared by the client fixture below, but Postgres
    state otherwise survives across test runs (and even across separate
    pytest invocations) since it's a real external database, not per-process
    state -- without this, a finding's history accumulates across runs.
    """

    with SessionLocal() as session:
        session.execute(text(f"TRUNCATE {', '.join(_PERSISTED_TABLES)} CASCADE"))
        session.commit()


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for finding persistence checks."""
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


def _create_analysis_payload(repository: str) -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": repository,
        "pull_request_number": 7,
        "commit_sha": "c" * 40,
        "trigger": "pull_request",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "app/routes/admin.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _create_finding(client: TestClient, repository: str) -> dict[str, object]:
    response = client.post("/analyses", json=_create_analysis_payload(repository))
    assert response.status_code == 202
    analysis = response.json()

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")
    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings
    return findings[0]


def _finding_rows_by_fingerprint(fingerprint: str) -> list[FindingModel]:
    # Eager-load history: the session closes at the end of this function, and
    # a lazy load on a detached instance would raise DetachedInstanceError.
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(FindingModel)
                .where(FindingModel.fingerprint == fingerprint)
                .options(selectinload(FindingModel.history)),
            ),
        )


@pytest.mark.integration
def test_repeated_scan_upserts_a_single_finding_row(client: TestClient) -> None:
    repository = "secureops/persistence-upsert"

    first_finding = _create_finding(client, repository)
    second_finding = _create_finding(client, repository)

    fingerprint = first_finding["fingerprint"]
    assert second_finding["fingerprint"] == fingerprint

    rows = _finding_rows_by_fingerprint(fingerprint)
    assert len(rows) == 1
    assert rows[0].status.value == "open"


@pytest.mark.integration
def test_override_survives_a_repeated_scan(client: TestClient) -> None:
    repository = "secureops/persistence-override"

    finding = _create_finding(client, repository)
    override_response = client.post(
        f"/findings/{finding['id']}/override",
        json={
            "changed_by": "security-reviewer@example.com",
            "change_type": "status_change",
            "to_value": "false_positive",
            "reason": "Validated as framework-sanitized input.",
        },
    )
    assert override_response.status_code == 200

    # Re-scan: a fresh scan always rebuilds findings with status OPEN. The
    # persisted row must keep the reviewer's decision, not reset to OPEN.
    _create_finding(client, repository)

    rows = _finding_rows_by_fingerprint(finding["fingerprint"])
    assert len(rows) == 1
    assert rows[0].status.value == "false_positive"
    assert len(rows[0].history) == 1
    assert rows[0].history[0].reason == "Validated as framework-sanitized input."
