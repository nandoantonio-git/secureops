"""Deterministic remediation fallback when contextual generation is unavailable."""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.models.enums import RecommendationConfidence, RecommendationSource
from app.remediation.templates import (
    RemediationRecommendation,
    RemediationTemplateContext,
    render_template,
    select_template,
)


@dataclass(frozen=True)
class _DeterministicGuidance:
    """Local remediation text for a deterministic finding family."""

    impact: str
    recommended_correction: str
    safe_example: str


@dataclass(frozen=True)
class RemediationFallbackContext:
    """Finding details used to produce local remediation guidance."""

    rule_id: str
    category: str | None
    language: str
    file_path: str
    line_start: int
    evidence: str
    sink: str | None = None
    user_input: str | None = None
    fallback_reason: str = "fallback"
    fallback_enabled: bool = True


_RULE_GUIDANCE: dict[str, _DeterministicGuidance] = {
    "python.yaml.unsafe_load": _DeterministicGuidance(
        impact=(
            "Unsafe deserialization can instantiate attacker-controlled data "
            "structures or objects and may lead to code execution or data "
            "tampering."
        ),
        recommended_correction=(
            "Replace yaml.load with yaml.safe_load for untrusted YAML input. "
            "If custom types are required, define an explicit allowlist of "
            "constructors instead of using a general-purpose loader."
        ),
        safe_example="import yaml\n\nparsed = yaml.safe_load({user_input})",
    ),
    "javascript.eval": _DeterministicGuidance(
        impact=(
            "Dynamic code execution can let attacker-controlled text run as "
            "application code in the user's browser or server runtime."
        ),
        recommended_correction=(
            "Remove eval-style execution for untrusted data. Map allowed "
            "actions to explicit functions, validate the selected action, and "
            "treat the input as data rather than executable code."
        ),
        safe_example=(
            "const handlers = {{ refresh: refreshDashboard }};\n"
            "const handler = handlers[String({user_input})];\n"
            "if (!handler) throw new Error(\"Unsupported action\");\n"
            "handler();"
        ),
    ),
}

_CATEGORY_GUIDANCE: dict[str, _DeterministicGuidance] = {
    "cwe-502": _RULE_GUIDANCE["python.yaml.unsafe_load"],
    "cwe-94": _RULE_GUIDANCE["javascript.eval"],
    "cwe-95": _RULE_GUIDANCE["javascript.eval"],
}


def build_fallback_recommendation(
    context: RemediationFallbackContext,
) -> RemediationRecommendation | None:
    """Build local remediation guidance, preferring reviewed templates."""

    if not context.fallback_enabled:
        return None

    template = select_template(
        rule_id=context.rule_id,
        category=context.category,
        language=context.language,
    )
    template_context = RemediationTemplateContext(
        file_path=context.file_path,
        line_start=context.line_start,
        language=context.language,
        evidence=context.evidence,
        sink=context.sink,
        user_input=context.user_input,
    )
    if template is not None:
        return _with_fallback_reason(
            render_template(template, template_context),
            context,
        )

    guidance = _select_guidance(context)
    return RemediationRecommendation(
        cause=_fallback_cause(context),
        evidence=_fallback_evidence(context),
        impact=guidance.impact,
        recommended_correction=_render_guidance(
            guidance.recommended_correction,
            context,
        ),
        safe_example=_render_guidance(
            guidance.safe_example,
            context,
            code_example=True,
        ),
        generation_source=RecommendationSource.DETERMINISTIC_FALLBACK,
        template_id=None,
        confidence=RecommendationConfidence.MEDIUM,
    )


def _with_fallback_reason(
    recommendation: RemediationRecommendation,
    context: RemediationFallbackContext,
) -> RemediationRecommendation:
    return replace(
        recommendation,
        evidence=(
            f"Fallback reason: {_fallback_reason(context)}. "
            f"{recommendation.evidence}"
        ),
    )


def _fallback_cause(context: RemediationFallbackContext) -> str:
    return (
        f"{_user_input(context)} reaches {_sink(context)} at "
        f"{_location(context)}. "
        "The pattern matched a deterministic security rule and needs a safer "
        "data-handling path."
    )


def _fallback_evidence(context: RemediationFallbackContext) -> str:
    parts = [
        f"Fallback reason: {_fallback_reason(context)}.",
        f"Finding at {_location(context)}.",
    ]
    if context.sink:
        parts.append(f"Sink: {context.sink}.")
    if context.evidence:
        parts.append(f"Evidence: {context.evidence}")
    return " ".join(parts)


def _select_guidance(context: RemediationFallbackContext) -> _DeterministicGuidance:
    rule_guidance = _RULE_GUIDANCE.get(_normalize(context.rule_id))
    if rule_guidance is not None:
        return rule_guidance

    category_guidance = _CATEGORY_GUIDANCE.get(_normalize(context.category))
    if category_guidance is not None:
        return category_guidance

    return _generic_guidance(context)


def _generic_guidance(context: RemediationFallbackContext) -> _DeterministicGuidance:
    sink = _sink(context)
    return _DeterministicGuidance(
        impact=(
            "The vulnerable pattern can let attacker-controlled data cross a "
            "trust boundary without the expected validation or encoding."
        ),
        recommended_correction=(
            f"Validate the data before it reaches {sink}, use the safe API for "
            "this operation, and keep untrusted input separate from executable "
            "or interpreted content."
        ),
        safe_example="validated_value = validate_untrusted_input(value)",
    )


def _render_guidance(
    template: str,
    context: RemediationFallbackContext,
    *,
    code_example: bool = False,
) -> str:
    user_input = _example_input(context) if code_example else _user_input(context)
    return template.format(
        sink=_sink(context),
        user_input=user_input,
        location=_location(context),
    )


def _fallback_reason(context: RemediationFallbackContext) -> str:
    return _non_empty(context.fallback_reason) or "fallback"


def _sink(context: RemediationFallbackContext) -> str:
    return _non_empty(context.sink) or _non_empty(context.rule_id) or "the sink"


def _user_input(context: RemediationFallbackContext) -> str:
    return _non_empty(context.user_input) or "untrusted input"


def _example_input(context: RemediationFallbackContext) -> str:
    candidate = _non_empty(context.user_input)
    if candidate and " " not in candidate:
        return candidate

    rule_id = _normalize(context.rule_id)
    if rule_id == "python.yaml.unsafe_load":
        return "raw_yaml"
    if _normalize(context.language) == "javascript":
        return "action"
    return "value"


def _location(context: RemediationFallbackContext) -> str:
    return f"{context.file_path}:{context.line_start}"


def _normalize(value: str | None) -> str:
    return (_non_empty(value) or "").lower()


def _non_empty(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


__all__ = [
    "RemediationFallbackContext",
    "build_fallback_recommendation",
]
