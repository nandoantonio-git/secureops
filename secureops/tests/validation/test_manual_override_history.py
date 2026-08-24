"""Validation for quickstart Scenario 7 manual override and history."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import analyses
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for manual override validation."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()


def _manual_override_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 107,
        "commit_sha": "7" * 40,
        "trigger": "manual_validation",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "app/routes/admin.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _create_analysis_with_findings(
    client: TestClient,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    create_response = client.post("/analyses", json=_manual_override_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings
    return analysis, findings


@pytest.mark.validation
def test_quickstart_scenario_7_manual_override_and_history(
    client: TestClient,
) -> None:
    _analysis, findings = _create_analysis_with_findings(client)
    original_finding = findings[0]
    override_payload = {
        "changed_by": "security-reviewer@example.com",
        "change_type": "status_change",
        "to_value": "accepted_risk",
        "reason": "Temporary exposure accepted for the controlled rollout.",
    }

    override_response = client.post(
        f"/findings/{original_finding['id']}/override",
        json=override_payload,
    )

    assert override_response.status_code == 200
    overridden = override_response.json()
    assert overridden["id"] == original_finding["id"]
    assert overridden["status"] == "accepted_risk"
    assert overridden["history"]

    history_entry = overridden["history"][-1]
    assert history_entry["changed_by"] == "security-reviewer@example.com"
    assert history_entry["change_type"] == "status_change"
    assert history_entry["from_value"] == "open"
    assert history_entry["to_value"] == "accepted_risk"
    assert (
        history_entry["reason"]
        == "Temporary exposure accepted for the controlled rollout."
    )
    assert history_entry["created_at"]

    _rerun_analysis, rerun_findings = _create_analysis_with_findings(client)
    rerun_finding = next(
        finding
        for finding in rerun_findings
        if finding["fingerprint"] == original_finding["fingerprint"]
    )

    assert rerun_finding["status"] == "accepted_risk"
    assert any(
        entry["to_value"] == "accepted_risk"
        and entry["reason"] == override_payload["reason"]
        for entry in rerun_finding["history"]
    )
