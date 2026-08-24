"""Python taint analysis from untrusted request inputs to sensitive sinks."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from app.engine.rules.python import PythonRuleFinding
from app.models.enums import FindingSource, Severity

LANGUAGE = "python"

_REQUEST_SOURCE_ATTRIBUTES = {
    "args",
    "cookies",
    "data",
    "files",
    "form",
    "headers",
    "json",
    "values",
}
_REQUEST_SOURCE_METHODS = {
    "get_data",
    "get_json",
}
_REQUEST_SOURCE_NAMES = {
    f"request.{attribute}" for attribute in _REQUEST_SOURCE_ATTRIBUTES
}
_SQL_SINK_METHODS = {
    "execute",
    "executemany",
}
_SQL_KEYWORDS = {
    "alter",
    "delete",
    "drop",
    "insert",
    "select",
    "update",
}


@dataclass(frozen=True)
class _Taint:
    source: str


def detect_python_taint_flows(file_path: str | Path) -> list[PythonRuleFinding]:
    """Return taint findings for Python source in a file."""

    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    return detect_python_taint_flows_from_source(source, file_path=path)


def detect_python_taint_flows_from_source(
    source: str,
    *,
    file_path: str | Path,
) -> list[PythonRuleFinding]:
    """Return taint findings for Python source text."""

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    analyzer = _PythonTaintAnalyzer(source, file_path=str(file_path))
    return analyzer.analyze(tree)


class _PythonTaintAnalyzer:
    def __init__(self, source: str, *, file_path: str) -> None:
        self._source = source
        self._file_path = file_path

    def analyze(self, tree: ast.Module) -> list[PythonRuleFinding]:
        findings: list[PythonRuleFinding] = []
        self._analyze_statements(tree.body, {}, findings)
        return findings

    def _analyze_statements(
        self,
        statements: list[ast.stmt],
        tainted_names: dict[str, _Taint],
        findings: list[PythonRuleFinding],
    ) -> None:
        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_function(statement, findings)
            elif isinstance(statement, ast.ClassDef):
                continue
            elif isinstance(statement, ast.Assign):
                self._find_sinks(statement, tainted_names, findings)
                self._analyze_assign(statement.targets, statement.value, tainted_names)
            elif isinstance(statement, ast.AnnAssign):
                self._find_sinks(statement, tainted_names, findings)
                targets = [statement.target] if statement.value is not None else []
                if statement.value is not None:
                    self._analyze_assign(targets, statement.value, tainted_names)
            elif isinstance(statement, ast.AugAssign):
                self._find_sinks(statement, tainted_names, findings)
                self._analyze_aug_assign(statement, tainted_names)
            elif isinstance(statement, ast.If):
                self._analyze_branch(statement.body, tainted_names, findings)
                self._analyze_branch(statement.orelse, tainted_names, findings)
            elif isinstance(statement, (ast.For, ast.AsyncFor)):
                self._analyze_loop(statement, tainted_names, findings)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                self._analyze_statements(statement.body, tainted_names, findings)
            elif isinstance(statement, ast.Try):
                self._analyze_try(statement, tainted_names, findings)
            else:
                self._find_sinks(statement, tainted_names, findings)

    def _analyze_function(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        findings: list[PythonRuleFinding],
    ) -> None:
        local_taint: dict[str, _Taint] = {}
        self._analyze_statements(statement.body, local_taint, findings)

    def _analyze_branch(
        self,
        statements: list[ast.stmt],
        tainted_names: dict[str, _Taint],
        findings: list[PythonRuleFinding],
    ) -> None:
        branch_taint = dict(tainted_names)
        self._analyze_statements(statements, branch_taint, findings)
        tainted_names.update(branch_taint)

    def _analyze_loop(
        self,
        statement: ast.For | ast.AsyncFor,
        tainted_names: dict[str, _Taint],
        findings: list[PythonRuleFinding],
    ) -> None:
        value_taint = self._expr_taint(statement.iter, tainted_names)
        if value_taint is not None:
            self._assign_target(statement.target, value_taint, tainted_names)
        self._analyze_branch(statement.body, tainted_names, findings)
        self._analyze_branch(statement.orelse, tainted_names, findings)

    def _analyze_try(
        self,
        statement: ast.Try,
        tainted_names: dict[str, _Taint],
        findings: list[PythonRuleFinding],
    ) -> None:
        self._analyze_branch(statement.body, tainted_names, findings)
        for handler in statement.handlers:
            self._analyze_branch(handler.body, tainted_names, findings)
        self._analyze_branch(statement.orelse, tainted_names, findings)
        self._analyze_branch(statement.finalbody, tainted_names, findings)

    def _analyze_assign(
        self,
        targets: list[ast.expr],
        value: ast.expr,
        tainted_names: dict[str, _Taint],
    ) -> None:
        value_taint = self._expr_taint(value, tainted_names)
        for target in targets:
            if value_taint is None:
                self._clear_target(target, tainted_names)
            else:
                self._assign_target(target, value_taint, tainted_names)

    def _analyze_aug_assign(
        self,
        statement: ast.AugAssign,
        tainted_names: dict[str, _Taint],
    ) -> None:
        target_taint = self._expr_taint(statement.target, tainted_names)
        value_taint = self._expr_taint(statement.value, tainted_names)
        combined_taint = target_taint or value_taint
        if combined_taint is None:
            self._clear_target(statement.target, tainted_names)
        else:
            self._assign_target(statement.target, combined_taint, tainted_names)

    def _find_sinks(
        self,
        statement: ast.AST,
        tainted_names: dict[str, _Taint],
        findings: list[PythonRuleFinding],
    ) -> None:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call) or not node.args:
                continue

            sink = _sql_sink_name(node)
            if sink is None:
                continue

            sql_arg = node.args[0]
            taint = self._expr_taint(sql_arg, tainted_names)
            if taint is None:
                continue
            if not _looks_like_sql(sql_arg):
                continue

            evidence = _source_segment(self._source, node)
            line_start, line_end = _line_range(node)
            findings.append(
                PythonRuleFinding(
                    file_path=self._file_path,
                    line_start=line_start,
                    line_end=line_end,
                    language=LANGUAGE,
                    rule_id="python.sql.tainted_execute",
                    category="CWE-89",
                    severity=Severity.CRITICAL,
                    source=FindingSource.PRIMARY_LANGUAGE_TAINT,
                    evidence=evidence,
                    sink=sink,
                    user_input=taint.source,
                ),
            )

    def _expr_taint(
        self,
        expression: ast.AST,
        tainted_names: dict[str, _Taint],
    ) -> _Taint | None:
        source_name = _request_source_name(expression)
        if source_name is not None:
            return _Taint(source=source_name)

        if isinstance(expression, ast.Name):
            return tainted_names.get(expression.id)

        if isinstance(expression, ast.NamedExpr):
            value_taint = self._expr_taint(expression.value, tainted_names)
            if value_taint is not None:
                self._assign_target(expression.target, value_taint, tainted_names)
            return value_taint

        if isinstance(expression, ast.Call):
            function_taint = self._expr_taint(expression.func, tainted_names)
            return function_taint or self._first_tainted_child(
                [*expression.args, *(keyword.value for keyword in expression.keywords)],
                tainted_names,
            )

        child_expressions = (
            child for child in ast.iter_child_nodes(expression)
            if isinstance(child, ast.expr)
        )
        return self._first_tainted_child(child_expressions, tainted_names)

    def _first_tainted_child(
        self,
        expressions: Iterable[ast.AST],
        tainted_names: dict[str, _Taint],
    ) -> _Taint | None:
        for expression in expressions:
            if not isinstance(expression, ast.AST):
                continue
            taint = self._expr_taint(expression, tainted_names)
            if taint is not None:
                return taint
        return None

    def _assign_target(
        self,
        target: ast.AST,
        taint: _Taint,
        tainted_names: dict[str, _Taint],
    ) -> None:
        if isinstance(target, ast.Name):
            tainted_names[target.id] = taint
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._assign_target(element, taint, tainted_names)

    def _clear_target(
        self,
        target: ast.AST,
        tainted_names: dict[str, _Taint],
    ) -> None:
        if isinstance(target, ast.Name):
            tainted_names.pop(target.id, None)
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._clear_target(element, tainted_names)


def _request_source_name(expression: ast.AST) -> str | None:
    if isinstance(expression, ast.Subscript):
        return _request_source_name(expression.value)

    if (
        isinstance(expression, ast.Attribute)
        and expression.attr in _REQUEST_SOURCE_ATTRIBUTES
    ):
        if _call_name(expression.value) == "request":
            return f"request.{expression.attr}"

    if isinstance(expression, ast.Call):
        call_name = _call_name(expression.func)
        if call_name is None:
            return None
        if call_name == "request.get" or any(
            call_name == f"request.{method}" for method in _REQUEST_SOURCE_METHODS
        ):
            return call_name
        if call_name.startswith("request.") and call_name.endswith(".get"):
            source_name = call_name.removesuffix(".get")
            if source_name in _REQUEST_SOURCE_NAMES:
                return source_name

    return None


def _sql_sink_name(node: ast.Call) -> str | None:
    name = _call_name(node.func)
    if name is None:
        return None

    _, _, method_name = name.rpartition(".")
    if method_name not in _SQL_SINK_METHODS:
        return None
    return name


def _looks_like_sql(expression: ast.AST) -> bool:
    literal_parts = _string_literals(expression)
    if not literal_parts:
        return True

    text = " ".join(literal_parts).lower()
    return any(keyword in text for keyword in _SQL_KEYWORDS)


def _string_literals(expression: ast.AST) -> list[str]:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return [expression.value]

    if isinstance(expression, ast.JoinedStr):
        parts: list[str] = []
        for value in expression.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
        return parts

    parts = []
    for child in ast.iter_child_nodes(expression):
        if isinstance(child, ast.expr):
            parts.extend(_string_literals(child))
    return parts


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return None


def _source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment is not None:
        return segment.strip()

    if not hasattr(node, "lineno"):
        return ""

    lines = source.splitlines()
    line_start, line_end = _line_range(node)
    return "\n".join(lines[line_start - 1 : line_end]).strip()


def _line_range(node: ast.AST) -> tuple[int, int]:
    line_start = int(getattr(node, "lineno", 1))
    line_end = int(getattr(node, "end_lineno", line_start))
    return line_start, line_end


__all__ = [
    "detect_python_taint_flows",
    "detect_python_taint_flows_from_source",
]
