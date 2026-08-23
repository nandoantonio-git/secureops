"""Deterministic secondary-language vulnerability rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.engine.parser import (
    DEFAULT_SECONDARY_LANGUAGE,
    ParserError,
    iter_nodes,
    parse_file,
    parse_source,
)
from app.models.enums import FindingSource, Severity

LANGUAGE = DEFAULT_SECONDARY_LANGUAGE

_HTML_ASSIGNMENT_SINKS = {
    "innerHTML": "javascript.dom.inner_html",
    "outerHTML": "javascript.dom.outer_html",
}


@dataclass(frozen=True)
class SecondaryRuleFinding:
    """Finding emitted by a deterministic secondary-language rule."""

    file_path: str
    line_start: int
    line_end: int
    language: str
    rule_id: str
    category: str
    severity: Severity
    source: FindingSource
    evidence: str
    sink: str
    user_input: str | None = None


def detect_secondary_vulnerabilities(
    file_path: str | Path,
) -> list[SecondaryRuleFinding]:
    """Return deterministic secondary-language findings for a source file."""

    path = Path(file_path)
    try:
        parsed = parse_file(path, language=LANGUAGE)
    except ParserError:
        return []

    return _detect_from_parsed_source(parsed, file_path=path)


def detect_secondary_vulnerabilities_from_source(
    source: str,
    *,
    file_path: str | Path,
    language: str = LANGUAGE,
) -> list[SecondaryRuleFinding]:
    """Return deterministic secondary-language findings for source text."""

    try:
        parsed = parse_source(source, language, file_path=file_path)
    except ParserError:
        return []

    return _detect_from_parsed_source(parsed, file_path=file_path)


def _detect_from_parsed_source(
    parsed: object,
    *,
    file_path: str | Path,
) -> list[SecondaryRuleFinding]:
    if getattr(parsed, "has_errors", False):
        return []

    findings: list[SecondaryRuleFinding] = []
    for node in iter_nodes(parsed.root_node, types=("assignment_expression",)):
        sink = _html_assignment_sink(parsed, node)
        if sink is None:
            continue

        line_start, line_end = parsed.line_range_for_node(node)
        findings.append(
            SecondaryRuleFinding(
                file_path=str(file_path),
                line_start=line_start,
                line_end=line_end,
                language=LANGUAGE,
                rule_id=_HTML_ASSIGNMENT_SINKS[sink],
                category="CWE-79",
                severity=Severity.HIGH,
                source=FindingSource.SECONDARY_LANGUAGE_RULE,
                evidence=parsed.text_for_node(node).strip(),
                sink=sink,
                user_input=_assigned_value_name(parsed, node),
            ),
        )

    return findings


def _html_assignment_sink(parsed: object, node: object) -> str | None:
    left = node.child_by_field_name("left")
    if left is None or left.type != "member_expression":
        return None

    property_node = left.child_by_field_name("property")
    if property_node is None:
        return None

    sink = parsed.text_for_node(property_node)
    if sink in _HTML_ASSIGNMENT_SINKS:
        return sink
    return None


def _assigned_value_name(parsed: object, node: object) -> str | None:
    right = node.child_by_field_name("right")
    if right is None:
        return None

    if right.type == "identifier":
        return parsed.text_for_node(right)

    identifiers = [
        parsed.text_for_node(child)
        for child in iter_nodes(right, types=("identifier",))
    ]
    if identifiers:
        return identifiers[0]
    return None


__all__ = [
    "SecondaryRuleFinding",
    "detect_secondary_vulnerabilities",
    "detect_secondary_vulnerabilities_from_source",
]
