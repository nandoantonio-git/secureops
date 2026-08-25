"""Unit tests for the AI severity re-classification suggestion.

Covers app/remediation/ollama_client.py's _parse_severity_suggestion and its
wiring into OllamaClient._recommendation_from_payload -- always optional,
never required, never applied automatically."""

from __future__ import annotations

from app.models.enums import RecommendationConfidence, RecommendationSource, Severity
from app.remediation.ollama_client import OllamaClient, _parse_severity_suggestion

_REQUIRED_FIELDS = {
    "cause": "Untrusted input reaches a sensitive sink.",
    "evidence": "cursor.execute(query)",
    "impact": "Attacker-controlled data can alter query behavior.",
    "recommended_correction": "Use parameterized queries.",
    "safe_example": "cursor.execute(query, params)",
    "confidence": "high",
}


def test_parse_severity_suggestion_ignores_agreement_with_current_severity() -> None:
    suggested, rationale = _parse_severity_suggestion(
        {"suggested_severity": "high", "severity_rationale": "matches"},
        current_severity="high",
    )

    assert suggested is None
    assert rationale is None


def test_parse_severity_suggestion_returns_a_real_disagreement() -> None:
    suggested, rationale = _parse_severity_suggestion(
        {
            "suggested_severity": "critical",
            "severity_rationale": "Reaches a raw SQL sink with no sanitization.",
        },
        current_severity="high",
    )

    assert suggested is Severity.CRITICAL
    assert rationale == "Reaches a raw SQL sink with no sanitization."


def test_parse_severity_suggestion_tolerates_missing_or_invalid_values() -> None:
    assert _parse_severity_suggestion({}, current_severity="high") == (None, None)
    assert _parse_severity_suggestion(
        {"suggested_severity": "extremely bad"},
        current_severity="high",
    ) == (None, None)
    assert _parse_severity_suggestion(
        {"suggested_severity": 42},
        current_severity="high",
    ) == (None, None)


def test_recommendation_from_payload_surfaces_a_real_suggestion() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="codellama", timeout_seconds=5.0)
    body = dict(
        _REQUIRED_FIELDS,
        suggested_severity="critical",
        severity_rationale="Reaches a raw SQL sink with no sanitization.",
    )

    recommendation = client._recommendation_from_payload(
        {"response": body},
        current_severity="medium",
    )

    assert recommendation is not None
    assert recommendation.generation_source == RecommendationSource.OLLAMA_CONTEXTUALIZED
    assert recommendation.confidence == RecommendationConfidence.HIGH
    assert recommendation.suggested_severity == Severity.CRITICAL
    assert recommendation.severity_rationale == (
        "Reaches a raw SQL sink with no sanitization."
    )


def test_recommendation_from_payload_is_valid_without_a_severity_suggestion() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="codellama", timeout_seconds=5.0)

    recommendation = client._recommendation_from_payload(
        {"response": dict(_REQUIRED_FIELDS)},
        current_severity="medium",
    )

    assert recommendation is not None
    assert recommendation.suggested_severity is None
    assert recommendation.severity_rationale is None


def test_a_malformed_severity_suggestion_does_not_invalidate_the_recommendation() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="codellama", timeout_seconds=5.0)
    body = dict(_REQUIRED_FIELDS, suggested_severity="not-a-real-severity")

    recommendation = client._recommendation_from_payload(
        {"response": body},
        current_severity="medium",
    )

    assert recommendation is not None
    assert recommendation.suggested_severity is None
