"""Unit tests for rendering the AI severity suggestion in PR feedback."""

from __future__ import annotations

from typing import Any

from app.github.comments import format_pr_feedback


def _finding(**remediation_overrides: Any) -> dict[str, Any]:
    return {
        "id": "finding-1",
        "file_path": "app/routes/refunds.py",
        "line_start": 12,
        "language": "python",
        "rule_id": "python.sql.tainted_execute",
        "category": "CWE-89",
        "severity": "medium",
        "status": "open",
        "source": "primary_language_taint",
        "remediation": {
            "cause": "Untrusted input reaches cursor.execute.",
            "evidence": "cursor.execute(query)",
            "impact": "Attacker-controlled data can alter query behavior.",
            "recommended_correction": "Use parameterized queries.",
            "safe_example": "cursor.execute(query, params)",
            **remediation_overrides,
        },
    }


def test_renders_a_real_severity_suggestion_as_non_authoritative() -> None:
    comment = format_pr_feedback(
        findings=[
            _finding(
                suggested_severity="critical",
                severity_rationale="Reaches a raw SQL sink with no sanitization.",
            ),
        ],
        mode="advisory",
    )

    assert "AI severity suggestion (not applied automatically)" in comment
    assert "`critical` instead of `medium`" in comment
    assert "Reaches a raw SQL sink with no sanitization." in comment
    assert "POST /findings/finding-1/override" in comment
    assert "severity_override" in comment


def test_omits_the_suggestion_block_when_there_is_no_suggestion() -> None:
    comment = format_pr_feedback(findings=[_finding()], mode="advisory")

    assert "AI severity suggestion" not in comment


def test_omits_the_suggestion_block_when_the_model_agrees_with_the_rule() -> None:
    # The parser (ollama_client._parse_severity_suggestion) already drops
    # agreement before it reaches the recommendation -- this proves the
    # renderer treats a missing suggested_severity the same way regardless
    # of why it's missing.
    comment = format_pr_feedback(
        findings=[_finding(suggested_severity=None, severity_rationale=None)],
        mode="advisory",
    )

    assert "AI severity suggestion" not in comment
