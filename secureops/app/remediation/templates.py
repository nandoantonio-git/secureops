"""Reviewed remediation templates for deterministic vulnerability patterns."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import RecommendationConfidence, RecommendationSource


@dataclass(frozen=True)
class RemediationTemplateContext:
    """Finding details used to adapt reviewed guidance to a concrete location."""

    file_path: str
    line_start: int
    language: str
    evidence: str
    sink: str | None = None
    user_input: str | None = None


@dataclass(frozen=True)
class RemediationTemplate:
    """Reviewed remediation guidance for a known vulnerability pattern."""

    template_id: str
    language: str
    rule_ids: tuple[str, ...]
    categories: tuple[str, ...]
    impact: str
    confidence: RecommendationConfidence
    cause_template: str
    correction_template: str
    safe_example_template: str


@dataclass(frozen=True)
class RemediationRecommendation:
    """Rendered remediation recommendation matching the API/ORM field names."""

    cause: str
    evidence: str
    impact: str
    recommended_correction: str
    safe_example: str
    generation_source: RecommendationSource
    template_id: str | None
    confidence: RecommendationConfidence


_TEMPLATES: tuple[RemediationTemplate, ...] = (
    RemediationTemplate(
        template_id="python-command-injection",
        language="python",
        rule_ids=(
            "python.subprocess.shell_true",
            "python.os.system",
        ),
        categories=("CWE-78",),
        impact=(
            "Command injection can let an attacker execute operating system "
            "commands with the privileges of the application process."
        ),
        confidence=RecommendationConfidence.HIGH,
        cause_template=(
            "Untrusted input {user_input} is passed into {sink} at {location}. "
            "Building a shell command from request-controlled data allows the "
            "shell to interpret metacharacters as additional commands."
        ),
        correction_template=(
            "Replace the shell invocation with {sink} using an explicit "
            "argument list, validate the allowed operation, and pass only "
            "normalized values. Keep shell execution disabled and avoid "
            "concatenating user-controlled strings into a command."
        ),
        safe_example_template=(
            "from pathlib import Path\n"
            "import subprocess\n\n"
            "safe_name = Path({user_input}).name\n"
            "subprocess.run([\"convert\", safe_name], check=True)"
        ),
    ),
    RemediationTemplate(
        template_id="javascript-dom-xss",
        language="javascript",
        rule_ids=(
            "javascript.dom.inner_html",
            "javascript.dom.insert_adjacent_html",
        ),
        categories=("CWE-79",),
        impact=(
            "DOM XSS can let attacker-controlled data execute script in the "
            "user's browser and act with that user's session."
        ),
        confidence=RecommendationConfidence.HIGH,
        cause_template=(
            "Untrusted input {user_input} is written to {sink} at {location}. "
            "HTML-parsing DOM sinks treat attacker-controlled markup as page "
            "content, which can execute script."
        ),
        correction_template=(
            "Use textContent or DOM node creation APIs for untrusted values. "
            "If limited markup is required, sanitize with an approved HTML "
            "sanitizer before assigning to {sink}."
        ),
        safe_example_template=(
            "const value = String({user_input});\n"
            "results.replaceChildren();\n"
            "const item = document.createElement(\"strong\");\n"
            "item.textContent = value;\n"
            "results.appendChild(item);"
        ),
    ),
)


def select_template(
    *,
    rule_id: str | None,
    category: str | None,
    language: str | None,
) -> RemediationTemplate | None:
    """Return the reviewed template that best matches a finding."""

    normalized_language = _normalize(language)
    normalized_rule_id = _normalize(rule_id)
    normalized_category = _normalize(category)

    for template in _TEMPLATES:
        if template.language != normalized_language:
            continue
        if normalized_rule_id and _contains_normalized(
            template.rule_ids,
            normalized_rule_id,
        ):
            return template

    for template in _TEMPLATES:
        if template.language != normalized_language:
            continue
        if normalized_category and _contains_normalized(
            template.categories,
            normalized_category,
        ):
            return template

    return None


def render_template(
    template: RemediationTemplate,
    context: RemediationTemplateContext,
) -> RemediationRecommendation:
    """Render reviewed guidance for a specific finding context."""

    values = {
        "location": _location(context),
        "sink": context.sink or "the vulnerable sink",
        "user_input": context.user_input or "untrusted input",
    }
    return RemediationRecommendation(
        cause=template.cause_template.format(**values),
        evidence=_render_evidence(context),
        impact=template.impact,
        recommended_correction=template.correction_template.format(**values),
        safe_example=template.safe_example_template.format(**values),
        generation_source=RecommendationSource.REVIEWED_TEMPLATE,
        template_id=template.template_id,
        confidence=template.confidence,
    )


def reviewed_templates() -> tuple[RemediationTemplate, ...]:
    """Return the immutable reviewed template catalog."""

    return _TEMPLATES


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized.lower()


def _contains_normalized(values: tuple[str, ...], expected: str) -> bool:
    return any(_normalize(value) == expected for value in values)


def _location(context: RemediationTemplateContext) -> str:
    return f"{context.file_path}:{context.line_start}"


def _render_evidence(context: RemediationTemplateContext) -> str:
    parts = [f"Finding at {_location(context)}."]
    if context.sink:
        parts.append(f"Sink: {context.sink}.")
    if context.evidence:
        parts.append(f"Evidence: {context.evidence}")
    return " ".join(parts)


__all__ = [
    "RemediationRecommendation",
    "RemediationTemplate",
    "RemediationTemplateContext",
    "render_template",
    "reviewed_templates",
    "select_template",
]
