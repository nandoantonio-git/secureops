"""Validation for quickstart Scenario 4 restricted critical blocking."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import analyses
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for restricted blocking validation."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()


def _restricted_critical_payload() -> dict[str, object]:
    vulnerable_file = (
        FIXTURES_DIR
        / "python_vulnerable"
        / "critical_unprotected_data_flow.py"
    )
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 104,
        "commit_sha": "4" * 40,
        "trigger": "manual_validation",
        "mode": "blocking_enabled",
        "changed_files": [
            {
                "path": "app/invoices.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


@pytest.mark.validation
def test_quickstart_scenario_4_restricted_blocking_for_critical_evidence(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_restricted_critical_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"
    assert analysis["mode"] == "blocking_enabled"
    assert analysis["findings_count"] >= 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    critical_findings = [
        finding
        for finding in findings
        if finding["rule_id"] == "python.sql.tainted_execute"
    ]
    assert critical_findings

    critical_finding = critical_findings[0]
    assert critical_finding["severity"] == "critical"
    assert critical_finding["source"] == "primary_language_taint"

    signals = critical_finding["detection_signals"]
    assert len(signals) >= 2
    assert all(signal["deterministic"] is True for signal in signals)
    signal_types = {signal["signal_type"] for signal in signals}
    assert "deterministic_rule" in signal_types
    assert "data_flow" in signal_types
    assert "ai_assisted_classification" not in signal_types

    gate_response = client.get(f"/analyses/{analysis['id']}/gate-decision")

    assert gate_response.status_code == 200
    gate_decision = gate_response.json()
    assert gate_decision["analysis_id"] == analysis["id"]
    assert gate_decision["mode"] == "blocking_enabled"
    assert gate_decision["decision"] == "blocked"
    assert critical_finding["id"] in gate_decision["blocking_findings"]
