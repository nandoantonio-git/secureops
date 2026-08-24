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
            "javascript.dom.outer_html",
            "javascript.dom.insert_adjacent_html",
            "javascript.dom.document_write",
            "javascript.dom.document_writeln",
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
            "Replace {sink} with textContent or DOM node creation APIs for "
            "untrusted values. If limited markup is required, sanitize with "
            "an approved HTML sanitizer before sending content to an "
            "HTML-parsing sink."
        ),
        safe_example_template=(
            "const value = String({user_input});\n"
            "const item = document.createElement(\"span\");\n"
            "item.textContent = value;\n"
            "container.replaceChildren(item);"
        ),
    ),
    RemediationTemplate(
        template_id="python-unsafe-yaml-load",
        language="python",
        rule_ids=("python.yaml.unsafe_load",),
        categories=("CWE-502",),
        impact=(
            "Unsafe deserialization can instantiate attacker-controlled data "
            "structures or objects and may lead to code execution or data "
            "tampering."
        ),
        confidence=RecommendationConfidence.HIGH,
        cause_template=(
            "Untrusted YAML input {user_input} is passed into {sink} at "
            "{location}. A general-purpose YAML loader can construct Python "
            "objects from attacker-controlled tags instead of parsing the "
            "document as plain data."
        ),
        correction_template=(
            "Replace {sink} with yaml.safe_load for untrusted YAML input. If "
            "custom YAML types are required, register only the specific "
            "constructors the application accepts and reject every other tag."
        ),
        safe_example_template=(
            "import yaml\n\n"
            "parsed = yaml.safe_load({user_input})"
        ),
    ),
    RemediationTemplate(
        template_id="javascript-dynamic-code-execution",
        language="javascript",
        rule_ids=(
            "javascript.eval",
            "javascript.function_constructor",
        ),
        categories=("CWE-95",),
        impact=(
            "Dynamic code execution can let attacker-controlled text run as "
            "application code in the user's browser or server runtime."
        ),
        confidence=RecommendationConfidence.HIGH,
        cause_template=(
            "Untrusted input {user_input} reaches {sink} at {location}. "
            "Dynamic code execution treats attacker-controlled strings as "
            "program source, so injected syntax can run with application "
            "privileges."
        ),
        correction_template=(
            "Remove {sink} for untrusted data. Dispatch only to explicit "
            "allowlisted functions, validate the selected action, and keep "
            "request-controlled values as data rather than executable code."
        ),
        safe_example_template=(
            "const handlers = {{ refresh: refreshDashboard }};\n"
            "const handler = handlers[String({user_input})];\n"
            "if (!handler) throw new Error(\"Unsupported action\");\n"
            "handler();"
        ),
    ),
    RemediationTemplate(
        template_id="javascript-string-timer-execution",
        language="javascript",
        rule_ids=("javascript.timer.string_execution",),
        categories=("CWE-95",),
        impact=(
            "String-based timer execution can run attacker-controlled code "
            "after the timer fires, giving injected script access to the "
            "current page or runtime context."
        ),
        confidence=RecommendationConfidence.HIGH,
        cause_template=(
            "Untrusted input {user_input} is used as the code argument for "
            "{sink} at {location}. Passing a string to a timer evaluates that "
            "string as code instead of calling a fixed callback."
        ),
        correction_template=(
            "Pass a function reference or closure to {sink}, validate any "
            "user-selected operation against an allowlist, and keep the timer "
            "delay separate from untrusted action data."
        ),
        safe_example_template=(
            "const handlers = {{ refresh: refreshDashboard }};\n"
            "const handler = handlers[String({user_input})];\n"
            "if (!handler) throw new Error(\"Unsupported action\");\n"
            "setTimeout(() => handler(), delayMs);"
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
