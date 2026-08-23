"""Unit tests for Python taint data-flow analysis."""

from pathlib import Path

from app.engine.taint import detect_python_taint_flows
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


def test_request_argument_flow_to_cursor_execute_is_critical_sql_injection() -> None:
    fixture_path = (
        FIXTURES_DIR
        / "python_vulnerable"
        / "critical_unprotected_data_flow.py"
    )

    findings = detect_python_taint_flows(fixture_path)

    finding = _finding_by_rule_id(findings, "python.sql.tainted_execute")
    assert _field(finding, "language") == "python"
    assert _field(finding, "category") == "CWE-89"
    assert _field(finding, "severity") == Severity.CRITICAL
    assert _field(finding, "source") == FindingSource.PRIMARY_LANGUAGE_TAINT
    assert _field(finding, "file_path") == str(fixture_path)
    assert _field(finding, "line_start") == 10
    assert _field(finding, "line_end") == 10
    assert _field(finding, "sink") == "cursor.execute"
    assert _field(finding, "user_input") == "request.args"
    assert "cursor.execute(query)" in _field(finding, "evidence")


def test_parameterized_cursor_execute_does_not_report_tainted_sql() -> None:
    fixture_path = FIXTURES_DIR / "python_clean" / "safe_request_handler.py"

    assert detect_python_taint_flows(fixture_path) == []
