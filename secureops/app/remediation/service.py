"""Remediation recommendation orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from app.remediation.fallback import (
    RemediationFallbackContext,
    build_fallback_recommendation,
)
from app.remediation.ollama_client import (
    OllamaRemediationContext,
    generate_remediation,
)
from app.remediation.templates import RemediationRecommendation


_PUBLISHED_RECOMMENDATION_FIELDS = (
    "cause",
    "evidence",
    "impact",
    "recommended_correction",
    "safe_example",
)


def build_remediation_recommendation(
    *,
    finding: Any,
    evidence: str,
    sink: Optional[str],
    user_input: Optional[str],
    settings: Any,
) -> RemediationRecommendation:
    """Return a complete recommendation, falling back when Ollama is unsafe."""

    fallback_context = RemediationFallbackContext(
        rule_id=finding.rule_id,
        category=finding.category,
        language=finding.language,
        file_path=finding.file_path,
        line_start=finding.line_start,
        evidence=evidence,
        sink=sink,
        user_input=user_input,
        fallback_enabled=settings.ollama_fallback_enabled,
    )
    ollama_result = generate_remediation(
        settings=settings,
        context=OllamaRemediationContext(
            rule_id=finding.rule_id,
            category=finding.category,
            language=finding.language,
            file_path=finding.file_path,
            line_start=finding.line_start,
            evidence=evidence,
            current_severity=_severity_value(finding.severity),
            sink=sink,
            user_input=user_input,
        ),
    )
    if _has_published_fields(ollama_result.recommendation):
        return ollama_result.recommendation

    if ollama_result.recommendation is not None:
        fallback_reason = (
            ollama_result.fallback_reason or "ollama_incomplete_recommendation"
        )
    else:
        fallback_reason = ollama_result.fallback_reason or "ollama_unavailable"
    fallback_context = replace(
        fallback_context,
        fallback_reason=fallback_reason,
    )
    fallback = build_fallback_recommendation(fallback_context)
    if _has_published_fields(fallback):
        return fallback

    return _build_required_fallback(fallback_context)


def _severity_value(severity: Any) -> str:
    return getattr(severity, "value", severity)


def _has_published_fields(
    recommendation: RemediationRecommendation | None,
) -> bool:
    if recommendation is None:
        return False

    return all(
        isinstance(getattr(recommendation, field, None), str)
        and getattr(recommendation, field).strip()
        for field in _PUBLISHED_RECOMMENDATION_FIELDS
    )


def _build_required_fallback(
    context: RemediationFallbackContext,
) -> RemediationRecommendation:
    recommendation = build_fallback_recommendation(
        replace(
            context,
            fallback_reason="fallback_disabled_after_ollama_failure",
            fallback_enabled=True,
        ),
    )
    if not _has_published_fields(recommendation):
        raise RuntimeError("Remediation fallback did not produce a recommendation.")
    return recommendation


__all__ = ["build_remediation_recommendation"]
