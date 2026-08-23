"""Validation for quickstart Scenarios 2 and 3 language-depth coverage."""

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


def _python_data_flow_payload() -> dict[str, object]:
    vulnerable_file = (
        FIXTURES_DIR
        / "python_vulnerable"
        / "critical_unprotected_data_flow.py"
    )
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 202,
        "commit_sha": "2" * 40,
        "trigger": "manual_validation",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "app/invoices.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _secondary_language_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "secondary_vulnerable" / "dom_xss.js"
    return {
        "repository": "secureops/web-portal",
        "pull_request_number": 203,
        "commit_sha": "3" * 40,
        "trigger": "manual_validation",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "web/search.js",
                "language": "javascript",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _by_language(items: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(item["language"]): item for item in items}


def _assert_has_limitation(item: dict[str, object], expected: str) -> None:
    limitations = item["limitations"]
    assert isinstance(limitations, list)
    assert any(expected in str(limitation).lower() for limitation in limitations)


def _assert_actionable_text(value: object) -> None:
    assert isinstance(value, str)
    assert value.strip()


@pytest.mark.validation
def test_quickstart_scenario_2_python_data_flow_finding(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_python_data_flow_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"
    assert analysis["findings_count"] >= 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    data_flow_findings = [
        finding
        for finding in findings
        if finding["rule_id"] == "python.sql.tainted_execute"
    ]
    assert data_flow_findings

    finding = data_flow_findings[0]
    assert finding["file_path"] == "app/invoices.py"
    assert finding["language"] == "python"
    assert finding["severity"] == "critical"
    assert finding["source"] == "primary_language_taint"

    signal_types = {
        signal["signal_type"] for signal in finding["detection_signals"]
    }
    assert "deterministic_rule" in signal_types
    assert "data_flow" in signal_types
    assert all(signal["deterministic"] is True for signal in finding["detection_signals"])

    remediation = finding["remediation"]
    for field in (
        "cause",
        "evidence",
        "impact",
        "recommended_correction",
        "safe_example",
    ):
        _assert_actionable_text(remediation[field])

    remediation_text = " ".join(
        str(remediation[field]).lower()
        for field in ("cause", "evidence", "recommended_correction")
    )
    assert "request.args" in remediation_text
    assert "cursor.execute" in remediation_text


@pytest.mark.validation
def test_quickstart_scenario_3_secondary_language_deterministic_coverage(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_secondary_language_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"

    coverage_results = _by_language(analysis["language_coverage_results"])
    assert "javascript" in coverage_results
    javascript_result = coverage_results["javascript"]
    assert javascript_result["files_seen"] == 1
    assert javascript_result["files_analyzed"] == 1
    assert javascript_result["rules_applied"] >= 1
    _assert_has_limitation(javascript_result, "minimal deterministic")
    _assert_has_limitation(javascript_result, "no data-flow")

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    secondary_findings = [
        finding
        for finding in findings
        if finding["rule_id"] == "javascript.dom.inner_html"
    ]
    assert secondary_findings

    finding = secondary_findings[0]
    assert finding["file_path"] == "web/search.js"
    assert finding["language"] == "javascript"
    assert finding["source"] == "secondary_language_rule"
    assert any(
        signal["signal_type"] == "deterministic_rule"
        and signal["deterministic"] is True
        for signal in finding["detection_signals"]
    )

    feedback_response = client.get(f"/analyses/{analysis['id']}/pr-feedback")

    assert feedback_response.status_code == 200
    feedback = feedback_response.json()["comment"].lower()
    assert "javascript" in feedback
    assert "minimal deterministic" in feedback
    assert "not parity" in feedback
    assert "python data-flow" in feedback
