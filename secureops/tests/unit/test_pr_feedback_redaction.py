"""Unit tests for sensitive evidence redaction in PR feedback."""

from __future__ import annotations

from typing import Any

import pytest

from app.github.comments import format_pr_feedback


SENSITIVE_EVIDENCE_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "hardcoded-secret",
        "file_path": "app/settings.py",
        "line_start": 14,
        "evidence": (
            'STRIPE_SECRET_KEY = "sk_example_redaction_fixture"'
        ),
        "forbidden_values": ("sk_example_redaction_fixture",),
        "context_terms": ("STRIPE_SECRET_KEY", "app/settings.py", "14"),
    },
    {
        "id": "github-token",
        "file_path": "scripts/deploy.py",
        "line_start": 22,
        "evidence": (
            'headers = {"Authorization": "Bearer '
            'github_token_redaction_fixture"}'
        ),
        "forbidden_values": ("github_token_redaction_fixture",),
        "context_terms": ("Authorization", "Bearer", "scripts/deploy.py", "22"),
    },
    {
        "id": "inline-credential",
        "file_path": "app/integrations.py",
        "line_start": 31,
        "evidence": (
            'requests.get(endpoint, auth=("admin", "SuperSecretPassword!"))'
        ),
        "forbidden_values": ("SuperSecretPassword!",),
        "context_terms": ("auth", "admin", "app/integrations.py", "31"),
    },
    {
        "id": "database-url",
        "file_path": "app/db.py",
        "line_start": 8,
        "evidence": (
            "DATABASE_URL = "
            '"postgresql://app_user:p@ssw0rd@db.internal:5432/payments"'
        ),
        "forbidden_values": ("app_user:p@ssw0rd",),
        "context_terms": (
            "DATABASE_URL",
            "postgresql://",
            "db.internal:5432/payments",
            "app/db.py",
            "8",
        ),
    },
    {
        "id": "private-key",
        "file_path": "app/crypto.py",
        "line_start": 40,
        "evidence": (
            'PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----\n'
            "MIIEpAIBAAKCAQEA7secretPrivateKeyMaterial\n"
            '-----END RSA PRIVATE KEY-----"""'
        ),
        "forbidden_values": ("MIIEpAIBAAKCAQEA7secretPrivateKeyMaterial",),
        "context_terms": ("PRIVATE_KEY", "RSA PRIVATE KEY", "app/crypto.py", "40"),
    },
)


def _finding(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_path": case["file_path"],
        "line_start": case["line_start"],
        "language": "python",
        "rule_id": "python.secrets.hardcoded",
        "category": "CWE-798",
        "severity": "high",
        "status": "open",
        "source": "primary_language_rule",
        "remediation": {
            "cause": "A sensitive value is embedded directly in source code.",
            "evidence": case["evidence"],
            "impact": (
                "Anyone with repository access can reuse the exposed secret."
            ),
            "recommended_correction": (
                "Move the value to a managed secret store or environment "
                "variable and rotate the exposed credential."
            ),
            "safe_example": (
                "secret_value = os.environ['SERVICE_SECRET_NAME']"
            ),
        },
    }


@pytest.mark.parametrize(
    "case",
    SENSITIVE_EVIDENCE_CASES,
    ids=[str(case["id"]) for case in SENSITIVE_EVIDENCE_CASES],
)
def test_pr_feedback_redacts_sensitive_evidence_and_keeps_context(
    case: dict[str, Any],
) -> None:
    comment = format_pr_feedback(findings=[_finding(case)], mode="advisory")

    assert "[REDACTED]" in comment
    for required_heading in (
        "Cause",
        "Evidence",
        "Impact",
        "Recommended correction",
        "Safe example",
    ):
        assert required_heading in comment

    for context_term in case["context_terms"]:
        assert context_term in comment

    for forbidden_value in case["forbidden_values"]:
        assert forbidden_value not in comment
