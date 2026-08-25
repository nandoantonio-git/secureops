"""Integration test: POST /analyses attempts to publish when a GitHub token
is configured, and never fails the response when it isn't (or when
publishing itself fails)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.api.analyses as analyses_module
from app.config import get_settings
from app.main import app

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _payload() -> dict[str, object]:
    vulnerable_file = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"
    return {
        "repository": "acme/widgets",
        "pull_request_number": 7,
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


def test_publishes_when_a_github_token_is_configured(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def _fake_publish(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(get_settings(), "github_token", "ghp_fake")
    monkeypatch.setattr(analyses_module, "publish_pr_feedback", _fake_publish)

    response = client.post("/analyses", json=_payload())

    assert response.status_code == 202
    assert len(calls) == 1
    assert calls[0]["repository"] == "acme/widgets"
    assert calls[0]["pull_request_number"] == 7
    assert calls[0]["token"] == "ghp_fake"
    assert "SecureOps PR feedback" in calls[0]["comment_body"]


def test_skips_publishing_without_a_github_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def _fake_publish(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(get_settings(), "github_token", None)
    monkeypatch.setattr(analyses_module, "publish_pr_feedback", _fake_publish)

    response = client.post("/analyses", json=_payload())

    assert response.status_code == 202
    assert len(calls) == 1
    assert calls[0]["token"] is None


def test_a_github_publish_failure_never_fails_the_analysis_response(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raising_publish(**_kwargs: object) -> None:
        raise RuntimeError("network is down")

    monkeypatch.setattr(get_settings(), "github_token", "ghp_fake")
    monkeypatch.setattr(analyses_module, "publish_pr_feedback", _raising_publish)

    response = client.post("/analyses", json=_payload())

    assert response.status_code == 202
