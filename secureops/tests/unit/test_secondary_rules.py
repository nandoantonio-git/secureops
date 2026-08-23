"""Unit tests for secondary-language deterministic vulnerability rules."""

from pathlib import Path

from app.engine.rules.secondary import detect_secondary_vulnerabilities
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


def test_secondary_vulnerable_fixture_detects_dom_inner_html_xss() -> None:
    fixture_path = FIXTURES_DIR / "secondary_vulnerable" / "dom_xss.js"

    findings = detect_secondary_vulnerabilities(fixture_path)

    finding = _finding_by_rule_id(findings, "javascript.dom.inner_html")
    assert _field(finding, "language") == "javascript"
    assert _field(finding, "category") == "CWE-79"
    assert _field(finding, "severity") == Severity.HIGH
    assert _field(finding, "source") == FindingSource.SECONDARY_LANGUAGE_RULE
    assert _field(finding, "file_path") == str(fixture_path)
    assert _field(finding, "line_start") == 5
    assert _field(finding, "line_end") == 5
    assert _field(finding, "sink") == "innerHTML"
    assert "results.innerHTML = `<strong>${term}</strong>`" in _field(
        finding,
        "evidence",
    )


def test_secondary_safe_fixture_has_no_deterministic_findings() -> None:
    fixture_path = FIXTURES_DIR / "secondary_clean" / "safe_dom_update.js"

    assert detect_secondary_vulnerabilities(fixture_path) == []
