"""Integration tests for manual finding override responses."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import analyses
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for finding override API checks."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()


def _create_analysis_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 42,
        "commit_sha": "b" * 40,
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


def _create_finding(client: TestClient) -> dict[str, object]:
    create_response = client.post("/analyses", json=_create_analysis_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings
    return findings[0]


@pytest.mark.integration
def test_override_finding_status_records_visible_history(
    client: TestClient,
) -> None:
    finding = _create_finding(client)
    override_payload = {
        "changed_by": "security-reviewer@example.com",
        "change_type": "status_change",
        "to_value": "false_positive",
        "reason": "Validated as framework-sanitized input.",
    }

    response = client.post(
        f"/findings/{finding['id']}/override",
        json=override_payload,
    )

    assert response.status_code == 200
    overridden = response.json()
    assert overridden["id"] == finding["id"]
    assert overridden["status"] == "false_positive"

    history = overridden["history"]
    assert len(history) == 1
    entry = history[0]
    assert entry["changed_by"] == "security-reviewer@example.com"
    assert entry["change_type"] == "status_change"
    assert entry["from_value"] == "open"
    assert entry["to_value"] == "false_positive"
    assert entry["reason"] == "Validated as framework-sanitized input."
    assert entry["created_at"]
