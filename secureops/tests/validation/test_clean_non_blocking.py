"""Validation for quickstart Scenario 5 clean-code non-blocking."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import analyses
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for clean-code gate validation."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()


def _clean_code_payload() -> dict[str, object]:
    python_file = FIXTURES_DIR / "python_clean" / "safe_request_handler.py"
    javascript_file = FIXTURES_DIR / "secondary_clean" / "safe_dom_update.js"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 105,
        "commit_sha": "5" * 40,
        "trigger": "manual_validation",
        "mode": "blocking_enabled",
        "changed_files": [
            {
                "path": "app/users.py",
                "language": "python",
                "content_ref": str(python_file),
            },
            {
                "path": "web/profile.js",
                "language": "javascript",
                "content_ref": str(javascript_file),
            },
        ],
    }


@pytest.mark.validation
def test_quickstart_scenario_5_clean_code_is_not_blocked(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_clean_code_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"
    assert analysis["mode"] == "blocking_enabled"
    assert analysis["findings_count"] == 0

    coverage_by_language = {
        result["language"]: result
        for result in analysis["language_coverage_results"]
    }
    assert coverage_by_language["python"]["files_analyzed"] == 1
    assert coverage_by_language["javascript"]["files_analyzed"] == 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings == []

    gate_response = client.get(f"/analyses/{analysis['id']}/gate-decision")

    assert gate_response.status_code == 200
    gate_decision = gate_response.json()
    assert gate_decision["analysis_id"] == analysis["id"]
    assert gate_decision["mode"] == "blocking_enabled"
    assert gate_decision["decision"] == "passed"
    assert gate_decision["blocking_findings"] == []
