"""Integration tests for analysis creation and structured finding feedback."""

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


def _create_analysis_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 42,
        "commit_sha": "f" * 40,
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


def _assert_non_empty_text(value: object) -> None:
    assert isinstance(value, str)
    assert value.strip()


@pytest.mark.integration
def test_create_analysis_then_list_structured_findings(client: TestClient) -> None:
    create_response = client.post("/analyses", json=_create_analysis_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["repository"] == "secureops/example-service"
    assert analysis["pull_request_number"] == 42
    assert analysis["commit_sha"] == "f" * 40
    assert analysis["trigger"] == "pull_request"
    assert analysis["mode"] == "advisory"
    assert analysis["status"] in {"requested", "running", "completed"}
    assert analysis["findings_count"] >= 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert isinstance(findings, list)
    assert len(findings) == analysis["findings_count"]

    finding = findings[0]
    assert finding["analysis_id"] == analysis["id"]
    assert finding["file_path"] == "app/routes/admin.py"
    assert finding["line_start"] >= 1
    assert finding["language"] == "python"
    _assert_non_empty_text(finding["rule_id"])
    assert finding["severity"] in {"critical", "high", "medium", "low", "info"}
    assert finding["status"] == "open"
    assert finding["source"] in {
        "primary_language_rule",
        "primary_language_taint",
        "validation_fixture",
    }

    remediation = finding["remediation"]
    for field in (
        "cause",
        "evidence",
        "impact",
        "recommended_correction",
        "safe_example",
    ):
        _assert_non_empty_text(remediation[field])
    assert remediation["generation_source"] in {
        "reviewed_template",
        "ollama_contextualized",
        "deterministic_fallback",
    }
    assert remediation["confidence"] in {"high", "medium", "low"}

    detection_signals = finding["detection_signals"]
    assert detection_signals
    assert any(signal["deterministic"] is True for signal in detection_signals)
    for signal in detection_signals:
        assert signal["signal_type"] in {
            "deterministic_rule",
            "data_flow",
            "template_match",
            "ai_assisted_classification",
        }
        assert isinstance(signal["deterministic"], bool)
        _assert_non_empty_text(signal["summary"])
