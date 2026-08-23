"""Integration tests for declared language coverage and visible limitations."""

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


def _coverage_payload() -> dict[str, object]:
    python_fixture = (
        FIXTURES_DIR
        / "python_vulnerable"
        / "critical_unprotected_data_flow.py"
    )
    javascript_fixture = FIXTURES_DIR / "secondary_vulnerable" / "dom_xss.js"
    return {
        "repository": "secureops/polyglot-service",
        "pull_request_number": 84,
        "commit_sha": "c" * 40,
        "trigger": "pull_request",
        "mode": "advisory",
        "changed_files": [
            {
                "path": "api/search.py",
                "language": "python",
                "content_ref": str(python_fixture),
            },
            {
                "path": "web/search.js",
                "language": "javascript",
                "content_ref": str(javascript_fixture),
            },
        ],
    }


def _by_language(items: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(item["language"]): item for item in items}


def _assert_has_limitation(item: dict[str, object], expected: str) -> None:
    limitations = item["limitations"]
    assert isinstance(limitations, list)
    assert any(expected in str(limitation).lower() for limitation in limitations)


@pytest.mark.integration
def test_analysis_declares_language_profiles_and_result_limitations(
    client: TestClient,
) -> None:
    response = client.post("/analyses", json=_coverage_payload())

    assert response.status_code == 202
    analysis = response.json()

    profiles = _by_language(analysis["language_coverage_profiles"])
    assert set(profiles) == {"python", "javascript"}

    python_profile = profiles["python"]
    assert python_profile["role"] == "primary"
    assert python_profile["coverage_level"] == "deep"
    assert python_profile["supports_data_flow"] is True
    assert "python.sql.tainted_execute" in python_profile["supported_rule_ids"]
    assert python_profile["limitations"] == []

    javascript_profile = profiles["javascript"]
    assert javascript_profile["role"] == "secondary"
    assert javascript_profile["coverage_level"] == "minimal_deterministic"
    assert javascript_profile["supports_data_flow"] is False
    assert "javascript.dom.inner_html" in javascript_profile["supported_rule_ids"]
    _assert_has_limitation(javascript_profile, "no data-flow")
    _assert_has_limitation(javascript_profile, "not parity")

    coverage_results = _by_language(analysis["language_coverage_results"])
    assert set(coverage_results) == {"python", "javascript"}

    python_result = coverage_results["python"]
    assert python_result["files_seen"] == 1
    assert python_result["files_analyzed"] == 1
    assert python_result["rules_applied"] >= 2
    assert python_result["limitations"] == []

    javascript_result = coverage_results["javascript"]
    assert javascript_result["files_seen"] == 1
    assert javascript_result["files_analyzed"] == 1
    assert javascript_result["rules_applied"] == 1
    _assert_has_limitation(javascript_result, "minimal deterministic")
    _assert_has_limitation(javascript_result, "no data-flow")
