"""Validation for quickstart Scenario 6 Ollama unavailable fallback."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Return a test client configured to exercise local fallback behavior."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "0.001")
    monkeypatch.setenv("OLLAMA_FALLBACK_ENABLED", "true")

    import app.config as config
    from app.main import app

    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    return TestClient(app)


def _ollama_unavailable_payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "secureops/example-service",
        "pull_request_number": 106,
        "commit_sha": "6" * 40,
        "trigger": "manual_validation",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "app/images.py",
                "language": "python",
                "content_ref": str(vulnerable_file),
            },
        ],
    }


def _assert_actionable_text(value: object) -> None:
    assert isinstance(value, str)
    assert value.strip()


@pytest.mark.validation
def test_quickstart_scenario_6_ollama_unavailable_uses_template_fallback(
    client: TestClient,
) -> None:
    create_response = client.post("/analyses", json=_ollama_unavailable_payload())

    assert create_response.status_code == 202
    analysis = create_response.json()
    assert analysis["status"] == "completed"
    assert analysis["failure_reason"] is None
    assert analysis["findings_count"] >= 1

    findings_response = client.get(f"/analyses/{analysis['id']}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert findings

    fallback_findings = [
        finding
        for finding in findings
        if finding["rule_id"] == "python.subprocess.shell_true"
    ]
    assert fallback_findings

    finding = fallback_findings[0]
    assert finding["file_path"] == "app/images.py"
    assert finding["language"] == "python"
    assert finding["status"] == "open"

    remediation = finding["remediation"]
    for field in (
        "cause",
        "evidence",
        "impact",
        "recommended_correction",
        "safe_example",
    ):
        _assert_actionable_text(remediation[field])

    assert remediation["generation_source"] == "reviewed_template"
    assert remediation["template_id"] == "python-command-injection"
    assert remediation["confidence"] == "high"
    assert "app/images.py" in remediation["evidence"]
    assert "shell=True" not in remediation["safe_example"]

    detection_signals = finding["detection_signals"]
    assert detection_signals
    assert any(signal["deterministic"] is True for signal in detection_signals)
