"""Deterministic Python vulnerability rules with source evidence extraction."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from app.models.enums import FindingSource, Severity

LANGUAGE = "python"

_SUBPROCESS_FUNCTIONS = {
    "run",
    "Popen",
    "call",
    "check_call",
    "check_output",
}


@dataclass(frozen=True)
class PythonRuleFinding:
    """Finding emitted by a deterministic Python rule."""

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
class _RuleMetadata:
    rule_id: str
    category: str
    severity: Severity
    sink: str


def detect_python_vulnerabilities(file_path: str | Path) -> list[PythonRuleFinding]:
    """Return deterministic Python vulnerability findings for a source file."""

    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    return detect_python_vulnerabilities_from_source(
        source,
        file_path=path,
    )


def detect_python_vulnerabilities_from_source(
    source: str,
    *,
    file_path: str | Path,
) -> list[PythonRuleFinding]:
    """Return deterministic Python vulnerability findings for source text."""

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    import_index = _ImportIndex.from_tree(tree)
    findings: list[PythonRuleFinding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        metadata = _match_call(node, import_index)
        if metadata is None:
            continue

        evidence = _source_segment(source, node)
        line_start, line_end = _line_range(node)
        findings.append(
            PythonRuleFinding(
                file_path=str(file_path),
                line_start=line_start,
                line_end=line_end,
                language=LANGUAGE,
                rule_id=metadata.rule_id,
                category=metadata.category,
                severity=metadata.severity,
                source=FindingSource.PRIMARY_LANGUAGE_RULE,
                evidence=evidence,
                sink=metadata.sink,
                user_input=_first_argument_name(node),
            ),
        )

    return findings


@dataclass(frozen=True)
class _ImportIndex:
    module_aliases: dict[str, str]
    symbol_aliases: dict[str, str]

    @classmethod
    def from_tree(cls, tree: ast.AST) -> _ImportIndex:
        module_aliases: dict[str, str] = {}
        symbol_aliases: dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                _index_import(node, module_aliases)
            elif isinstance(node, ast.ImportFrom):
                _index_import_from(node, symbol_aliases)

        return cls(
            module_aliases=module_aliases,
            symbol_aliases=symbol_aliases,
        )

    def resolve_call(self, node: ast.Call) -> str | None:
        name = _call_name(node.func)
        if name is None:
            return None

        if name in self.symbol_aliases:
            return self.symbol_aliases[name]

        root, _, suffix = name.partition(".")
        module = self.module_aliases.get(root)
        if module is None:
            return name
        if not suffix:
            return module
        return f"{module}.{suffix}"


def _index_import(node: ast.Import, module_aliases: dict[str, str]) -> None:
    for alias in node.names:
        root = alias.name.split(".", 1)[0]
        local_name = alias.asname or root
        module_aliases[local_name] = alias.name


def _index_import_from(
    node: ast.ImportFrom,
    symbol_aliases: dict[str, str],
) -> None:
    if not node.module:
        return

    for alias in node.names:
        if alias.name == "*":
            continue
        local_name = alias.asname or alias.name
        symbol_aliases[local_name] = f"{node.module}.{alias.name}"


def _match_call(
    node: ast.Call,
    import_index: _ImportIndex,
) -> _RuleMetadata | None:
    qualified_name = import_index.resolve_call(node)
    if qualified_name is None:
        return None

    subprocess_function = _subprocess_function(qualified_name)
    if subprocess_function and _has_true_keyword(node, "shell"):
        return _RuleMetadata(
            rule_id="python.subprocess.shell_true",
            category="CWE-78",
            severity=Severity.HIGH,
            sink=f"subprocess.{subprocess_function}",
        )

    if qualified_name == "os.system":
        return _RuleMetadata(
            rule_id="python.os.system",
            category="CWE-78",
            severity=Severity.HIGH,
            sink="os.system",
        )

    if qualified_name == "yaml.load" and not _uses_safe_yaml_loader(node):
        return _RuleMetadata(
            rule_id="python.yaml.unsafe_load",
            category="CWE-502",
            severity=Severity.MEDIUM,
            sink="yaml.load",
        )

    return None


def _subprocess_function(qualified_name: str) -> str | None:
    prefix = "subprocess."
    if not qualified_name.startswith(prefix):
        return None

    function_name = qualified_name.removeprefix(prefix)
    if function_name in _SUBPROCESS_FUNCTIONS:
        return function_name
    return None


def _has_true_keyword(node: ast.Call, name: str) -> bool:
    return any(
        keyword.arg == name and _is_true_literal(keyword.value)
        for keyword in node.keywords
    )


def _uses_safe_yaml_loader(node: ast.Call) -> bool:
    loader = _keyword_value(node, "Loader") or _keyword_value(node, "loader")
    if loader is None:
        return False

    loader_name = _call_name(loader)
    return loader_name in {
        "yaml.SafeLoader",
        "SafeLoader",
        "CSafeLoader",
        "yaml.CSafeLoader",
    }


def _keyword_value(node: ast.Call, name: str) -> ast.expr | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _is_true_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
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


def _first_argument_name(node: ast.Call) -> str | None:
    if not node.args:
        return None
    return _call_name(node.args[0])


__all__ = [
    "PythonRuleFinding",
    "detect_python_vulnerabilities",
    "detect_python_vulnerabilities_from_source",
]
