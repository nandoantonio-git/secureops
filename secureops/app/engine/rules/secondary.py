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

_HTML_METHOD_SINKS = {
    "insertAdjacentHTML": "javascript.dom.insert_adjacent_html",
}

_DOCUMENT_WRITE_SINKS = {
    "write": "javascript.dom.document_write",
    "writeln": "javascript.dom.document_writeln",
}

_DYNAMIC_CODE_SINKS = {
    "eval": "javascript.eval",
    "Function": "javascript.function_constructor",
}

_STRING_TIMER_SINKS = {
    "setInterval": "javascript.timer.string_execution",
    "setTimeout": "javascript.timer.string_execution",
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


@dataclass(frozen=True)
class _RuleMatch:
    rule_id: str
    category: str
    severity: Severity
    sink: str
    user_input: str | None


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
    for node in iter_nodes(
        parsed.root_node,
        types=("assignment_expression", "call_expression", "new_expression"),
    ):
        match = _match_rule(parsed, node)
        if match is None:
            continue

        line_start, line_end = parsed.line_range_for_node(node)
        findings.append(
            SecondaryRuleFinding(
                file_path=str(file_path),
                line_start=line_start,
                line_end=line_end,
                language=LANGUAGE,
                rule_id=match.rule_id,
                category=match.category,
                severity=match.severity,
                source=FindingSource.SECONDARY_LANGUAGE_RULE,
                evidence=parsed.text_for_node(node).strip(),
                sink=match.sink,
                user_input=match.user_input,
            ),
        )

    return findings


def _match_rule(parsed: object, node: object) -> _RuleMatch | None:
    if node.type == "assignment_expression":
        return _html_assignment_match(parsed, node)
    if node.type == "call_expression":
        return _call_expression_match(parsed, node)
    if node.type == "new_expression":
        return _new_expression_match(parsed, node)
    return None


def _html_assignment_match(parsed: object, node: object) -> _RuleMatch | None:
    sink = _html_assignment_sink(parsed, node)
    if sink is None:
        return None
    return _RuleMatch(
        rule_id=_HTML_ASSIGNMENT_SINKS[sink],
        category="CWE-79",
        severity=Severity.HIGH,
        sink=sink,
        user_input=_assigned_value_name(parsed, node),
    )


def _call_expression_match(parsed: object, node: object) -> _RuleMatch | None:
    callee = node.child_by_field_name("function")
    if callee is None:
        return None

    arguments = _argument_nodes(node)
    if callee.type == "identifier":
        sink = parsed.text_for_node(callee)
        if sink in _DYNAMIC_CODE_SINKS:
            return _dynamic_code_match(parsed, sink, arguments)
        if sink in _STRING_TIMER_SINKS:
            return _string_timer_match(parsed, sink, arguments)
        return None

    if callee.type != "member_expression":
        return None

    object_node = callee.child_by_field_name("object")
    property_node = callee.child_by_field_name("property")
    if object_node is None or property_node is None:
        return None

    object_name = parsed.text_for_node(object_node)
    property_name = parsed.text_for_node(property_node)
    if property_name in _HTML_METHOD_SINKS:
        return _RuleMatch(
            rule_id=_HTML_METHOD_SINKS[property_name],
            category="CWE-79",
            severity=Severity.HIGH,
            sink=property_name,
            user_input=_value_name(parsed, _argument_at(arguments, 1)),
        )
    if property_name in _DOCUMENT_WRITE_SINKS and _is_document_object(object_name):
        sink = f"document.{property_name}"
        return _RuleMatch(
            rule_id=_DOCUMENT_WRITE_SINKS[property_name],
            category="CWE-79",
            severity=Severity.HIGH,
            sink=sink,
            user_input=_value_name(parsed, _argument_at(arguments, 0)),
        )
    if property_name == "eval" and object_name in {"globalThis", "window"}:
        return _dynamic_code_match(parsed, "eval", arguments)
    return None


def _new_expression_match(parsed: object, node: object) -> _RuleMatch | None:
    constructor = node.child_by_field_name("constructor")
    if constructor is None:
        return None

    sink = parsed.text_for_node(constructor)
    if sink != "Function":
        return None
    return _dynamic_code_match(parsed, sink, _argument_nodes(node))


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


def _dynamic_code_match(
    parsed: object,
    sink: str,
    arguments: list[object],
) -> _RuleMatch:
    return _RuleMatch(
        rule_id=_DYNAMIC_CODE_SINKS[sink],
        category="CWE-95",
        severity=Severity.HIGH,
        sink=sink,
        user_input=_value_name(parsed, _dynamic_code_argument(sink, arguments)),
    )


def _string_timer_match(
    parsed: object,
    sink: str,
    arguments: list[object],
) -> _RuleMatch | None:
    code_argument = _argument_at(arguments, 0)
    if not _contains_string_code(code_argument):
        return None
    return _RuleMatch(
        rule_id=_STRING_TIMER_SINKS[sink],
        category="CWE-95",
        severity=Severity.HIGH,
        sink=sink,
        user_input=_value_name(parsed, code_argument),
    )


def _dynamic_code_argument(sink: str, arguments: list[object]) -> object | None:
    if not arguments:
        return None
    if sink == "Function":
        return arguments[-1]
    return arguments[0]


def _argument_nodes(node: object) -> list[object]:
    arguments = node.child_by_field_name("arguments")
    if arguments is None:
        return []
    return [
        child
        for child in getattr(arguments, "children", ())
        if getattr(child, "is_named", False)
    ]


def _argument_at(arguments: list[object], index: int) -> object | None:
    if index >= len(arguments):
        return None
    return arguments[index]


def _is_document_object(object_name: str) -> bool:
    return object_name == "document" or object_name.endswith(".document")


def _contains_string_code(node: object | None) -> bool:
    if node is None:
        return False
    if node.type in {"string", "template_string"}:
        return True
    for _string_node in iter_nodes(node, types=("string", "template_string")):
        return True
    return False


def _assigned_value_name(parsed: object, node: object) -> str | None:
    right = node.child_by_field_name("right")
    if right is None:
        return None

    return _value_name(parsed, right)


def _value_name(parsed: object, node: object | None) -> str | None:
    if node is None:
        return None

    if node.type == "identifier":
        return parsed.text_for_node(node)

    identifiers = [
        parsed.text_for_node(child)
        for child in iter_nodes(node, types=("identifier",))
    ]
    if identifiers:
        return identifiers[0]
    return None


__all__ = [
    "SecondaryRuleFinding",
    "detect_secondary_vulnerabilities",
    "detect_secondary_vulnerabilities_from_source",
]
