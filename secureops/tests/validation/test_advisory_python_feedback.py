"""Validation for quickstart Scenario 1 advisory Python PR feedback."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the SecureOps API."""
    return TestClient(app)


def _advisory_python_pr_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 101,
        "commit_sha": "a" * 40,
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


def _assert_actionable_text(value: object) -> None:
    assert isinstance(value, str)
    assert value.strip()


@pytest.mark.validation
def test_quickstart_scenario_1_advisory_python_pr_feedback(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_advisory_python_pr_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"
    assert analysis["mode"] == "advisory"
    assert analysis["findings_count"] >= 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings

    python_findings = [
        finding for finding in findings if finding["language"] == "python"
    ]
    assert python_findings
    python_finding = python_findings[0]
    assert python_finding["file_path"] == "app/routes/admin.py"
    assert python_finding["status"] == "open"
    assert python_finding["severity"] in {"critical", "high", "medium", "low"}

    remediation = python_finding["remediation"]
    for field in (
        "cause",
        "evidence",
        "impact",
        "recommended_correction",
        "safe_example",
    ):
        _assert_actionable_text(remediation[field])

    signals = python_finding["detection_signals"]
    assert signals
    assert any(signal["deterministic"] is True for signal in signals)

    gate_response = client.get(f"/analyses/{analysis['id']}/gate-decision")

    assert gate_response.status_code == 200
    gate_decision = gate_response.json()
    assert gate_decision["analysis_id"] == analysis["id"]
    assert gate_decision["mode"] == "advisory"
    assert gate_decision["decision"] == "advisory_only"
    assert gate_decision["blocking_findings"] == []
