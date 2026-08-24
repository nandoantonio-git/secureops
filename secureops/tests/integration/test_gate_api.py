"""Integration tests for analysis gate-decision responses."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import analyses
from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a clean test client for gate decision API checks."""
    analyses._ANALYSES.clear()
    analyses._FINDINGS_BY_ANALYSIS.clear()
    analyses._PR_FEEDBACK_BY_ANALYSIS.clear()
    try:
        yield TestClient(app)
    finally:
        analyses._ANALYSES.clear()
        analyses._FINDINGS_BY_ANALYSIS.clear()
        analyses._PR_FEEDBACK_BY_ANALYSIS.clear()


def _create_analysis_payload(mode: str) -> dict[str, object]:
    vulnerable_file = (
        FIXTURES_DIR
        / "python_vulnerable"
        / "critical_unprotected_data_flow.py"
    )
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 42,
        "commit_sha": "a" * 40,
        "trigger": "pull_request",
        "mode": mode,
        "changed_files": [
            {
                "path": "app/routes/invoices.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _create_analysis(client: TestClient, *, mode: str) -> dict[str, object]:
    response = client.post("/analyses", json=_create_analysis_payload(mode))

    assert response.status_code == 202
    analysis = response.json()
    assert analysis["mode"] == mode
    return analysis


@pytest.mark.integration
def test_gate_decision_is_advisory_only_in_advisory_mode(
    client: TestClient,
) -> None:
    analysis = _create_analysis(client, mode="advisory")

    response = client.get(f"/analyses/{analysis['id']}/gate-decision")

    assert response.status_code == 200
    decision = response.json()
    assert decision["analysis_id"] == analysis["id"]
    assert decision["mode"] == "advisory"
    assert decision["decision"] == "advisory_only"
    assert decision["reasons"]
    assert decision["blocking_findings"] == []


@pytest.mark.integration
def test_gate_decision_blocks_critical_deterministic_findings_in_blocking_mode(
    client: TestClient,
) -> None:
    analysis = _create_analysis(client, mode="blocking_enabled")

    response = client.get(f"/analyses/{analysis['id']}/gate-decision")

    assert response.status_code == 200
    decision = response.json()
    assert decision["analysis_id"] == analysis["id"]
    assert decision["mode"] == "blocking_enabled"
    assert decision["decision"] == "blocked"
    assert decision["reasons"]
    assert decision["blocking_findings"]

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")
    assert findings_response.status_code == 200
    findings_by_id = {
        finding["id"]: finding
        for finding in findings_response.json()
    }
    for finding_id in decision["blocking_findings"]:
        finding = findings_by_id[finding_id]
        assert finding["severity"] == "critical"
        deterministic_signals = [
            signal
            for signal in finding["detection_signals"]
            if signal["deterministic"] is True
        ]
        assert len(deterministic_signals) >= 2
