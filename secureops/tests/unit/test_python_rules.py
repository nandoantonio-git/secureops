"""Unit tests for Python deterministic vulnerability rules."""

from pathlib import Path

from app.engine.rules.python import detect_python_vulnerabilities
from app.models.enums import FindingSource, Severity


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _field(value: object, name: str) -> object:
    """Read fields from either dataclass/model instances or dict payloads."""
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _finding_by_rule_id(findings: list[object], rule_id: str) -> object:
    matches = [
        finding for finding in findings if _field(finding, "rule_id") == rule_id
    ]
    assert len(matches) == 1
    return matches[0]


def test_python_vulnerable_fixture_detects_shell_true_command_injection() -> None:
    fixture_path = FIXTURES_DIR / "python_vulnerable" / "command_injection.py"

    findings = detect_python_vulnerabilities(fixture_path)

    finding = _finding_by_rule_id(findings, "python.subprocess.shell_true")
    assert _field(finding, "language") == "python"
    assert _field(finding, "category") == "CWE-78"
    assert _field(finding, "severity") == Severity.HIGH
    assert _field(finding, "source") == FindingSource.PRIMARY_LANGUAGE_RULE
    assert _field(finding, "file_path") == str(fixture_path)
    assert _field(finding, "line_start") == 8
    assert _field(finding, "line_end") == 8
    assert _field(finding, "sink") == "subprocess.run"
    assert "subprocess.run(command, shell=True, check=True)" in _field(
        finding,
        "evidence",
    )


def test_python_safe_fixture_has_no_deterministic_findings() -> None:
    fixture_path = FIXTURES_DIR / "python_clean" / "safe_request_handler.py"

    assert detect_python_vulnerabilities(fixture_path) == []
