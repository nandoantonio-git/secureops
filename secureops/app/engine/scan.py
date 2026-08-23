"""Scan orchestration for changed pull request files."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.engine.fingerprint import build_finding_fingerprint
from app.engine.parser import (
    ParserError,
    UnsupportedLanguageError,
    detect_language,
    normalize_language,
    parse_source,
)
from app.engine.rules.python import (
    PythonRuleFinding,
    detect_python_vulnerabilities_from_source,
)
from app.models.enums import FindingStatus

if TYPE_CHECKING:
    from app.models.finding import Finding


@dataclass(frozen=True)
class ChangedFileCandidate:
    """Changed source file resolved from an API payload or local test object."""

    path: str
    language: str
    content_ref: str
    content: str | None = None


@dataclass(frozen=True)
class ScanSkippedFile:
    """A changed file that could not be analyzed."""

    path: str
    reason: str


@dataclass(frozen=True)
class ScannedFinding:
    """Finding plus rule evidence needed by later feedback/remediation steps."""

    finding: Finding
    evidence: str
    stable_anchor: str
    sink: str | None = None
    user_input: str | None = None


@dataclass(frozen=True)
class ScanResult:
    """Structured result of a changed-file scan."""

    findings: list[Finding]
    scanned_findings: list[ScannedFinding]
    parsed_files: int
    skipped_files: list[ScanSkippedFile]

    @property
    def findings_count(self) -> int:
        """Return the number of ORM findings created by the scan."""

        return len(self.findings)


def orchestrate_scan(
    analysis_id: str,
    repository: str,
    changed_files: Iterable[Any],
) -> ScanResult:
    """Parse changed files, run supported rules, and create ORM findings."""

    findings: list[Finding] = []
    scanned_findings: list[ScannedFinding] = []
    skipped_files: list[ScanSkippedFile] = []
    parsed_files = 0

    for raw_changed_file in changed_files:
        candidate = _coerce_changed_file(raw_changed_file)
        if candidate is None:
            skipped_files.append(
                ScanSkippedFile(path="<unknown>", reason="invalid_changed_file"),
            )
            continue

        try:
            source_text = _source_text(candidate)
        except OSError as exc:
            skipped_files.append(
                ScanSkippedFile(
                    path=candidate.path,
                    reason=f"content_unavailable: {exc}",
                ),
            )
            continue

        try:
            parsed = parse_source(
                source_text,
                candidate.language,
                file_path=candidate.path,
            )
        except UnsupportedLanguageError:
            skipped_files.append(
                ScanSkippedFile(path=candidate.path, reason="unsupported_language"),
            )
            continue
        except ParserError as exc:
            skipped_files.append(
                ScanSkippedFile(
                    path=candidate.path,
                    reason=f"parse_unavailable: {exc}",
                ),
            )
            continue

        parsed_files += 1
        rule_findings = _run_rules(
            source_text,
            language=parsed.language,
            file_path=candidate.path,
        )

        for rule_finding in rule_findings:
            scanned_finding = _create_scanned_finding(
                analysis_id=analysis_id,
                repository=repository,
                rule_finding=rule_finding,
            )
            findings.append(scanned_finding.finding)
            scanned_findings.append(scanned_finding)

    return ScanResult(
        findings=findings,
        scanned_findings=scanned_findings,
        parsed_files=parsed_files,
        skipped_files=skipped_files,
    )


def scan_changed_files(
    analysis_id: str,
    repository: str,
    changed_files: Iterable[Any],
) -> list[Finding]:
    """Return ORM findings created from changed files."""

    return orchestrate_scan(
        analysis_id,
        repository,
        changed_files,
    ).findings


def create_findings(
    analysis_id: str,
    repository: str,
    changed_files: Iterable[Any],
) -> list[Finding]:
    """Compatibility wrapper for callers that only need finding objects."""

    return scan_changed_files(analysis_id, repository, changed_files)


def scan_analysis(analysis: Any, changed_files: Iterable[Any]) -> ScanResult:
    """Run a scan for an analysis ORM object and attach created findings."""

    result = orchestrate_scan(
        str(analysis.id),
        str(analysis.repository),
        changed_files,
    )
    analysis.findings.extend(result.findings)
    return result


def _coerce_changed_file(raw_changed_file: Any) -> ChangedFileCandidate | None:
    path = _field(raw_changed_file, "path")
    content_ref = _field(raw_changed_file, "content_ref")
    language = _field(raw_changed_file, "language")
    content = _field(raw_changed_file, "content")

    if path is None or content_ref is None:
        return None

    path_text = str(path).strip()
    content_ref_text = str(content_ref).strip()
    if not path_text or not content_ref_text:
        return None

    try:
        language_text = normalize_language(str(language)) if language else ""
    except UnsupportedLanguageError:
        inferred_language = detect_language(path_text) or detect_language(
            content_ref_text,
        )
        if inferred_language is None:
            return ChangedFileCandidate(
                path=path_text,
                language=str(language),
                content_ref=content_ref_text,
                content=None if content is None else str(content),
            )
        language_text = inferred_language

    if not language_text:
        inferred_language = detect_language(path_text) or detect_language(
            content_ref_text,
        )
        if inferred_language is None:
            return ChangedFileCandidate(
                path=path_text,
                language="",
                content_ref=content_ref_text,
                content=None if content is None else str(content),
            )
        language_text = inferred_language

    return ChangedFileCandidate(
        path=path_text,
        language=language_text,
        content_ref=content_ref_text,
        content=None if content is None else str(content),
    )


def _source_text(candidate: ChangedFileCandidate) -> str:
    if candidate.content is not None:
        return candidate.content

    content_path = Path(candidate.content_ref)
    return content_path.read_text(encoding="utf-8")


def _run_rules(
    source_text: str,
    *,
    language: str,
    file_path: str,
) -> list[PythonRuleFinding]:
    if language == "python":
        return detect_python_vulnerabilities_from_source(
            source_text,
            file_path=file_path,
        )
    return []


def _create_scanned_finding(
    *,
    analysis_id: str,
    repository: str,
    rule_finding: PythonRuleFinding,
) -> ScannedFinding:
    from app.models.finding import Finding

    stable_anchor = _stable_anchor(rule_finding)
    fingerprint = build_finding_fingerprint(
        repository=repository,
        file_path=rule_finding.file_path,
        language=rule_finding.language,
        rule_id=rule_finding.rule_id,
        category=rule_finding.category,
        source=rule_finding.source.value,
        stable_anchor=stable_anchor,
        evidence=rule_finding.evidence,
        line_start=rule_finding.line_start,
        line_end=rule_finding.line_end,
    )
    finding = Finding(
        analysis_id=analysis_id,
        repository=repository,
        file_path=rule_finding.file_path,
        line_start=rule_finding.line_start,
        line_end=rule_finding.line_end,
        language=rule_finding.language,
        rule_id=rule_finding.rule_id,
        category=rule_finding.category,
        severity=rule_finding.severity,
        status=FindingStatus.OPEN,
        source=rule_finding.source,
        fingerprint=fingerprint,
    )
    return ScannedFinding(
        finding=finding,
        evidence=rule_finding.evidence,
        stable_anchor=stable_anchor,
        sink=rule_finding.sink,
        user_input=rule_finding.user_input,
    )


def _stable_anchor(rule_finding: PythonRuleFinding) -> str:
    parts = [
        rule_finding.rule_id,
        rule_finding.sink,
    ]
    if rule_finding.user_input:
        parts.append(rule_finding.user_input)
    else:
        parts.append(rule_finding.evidence)
    return ":".join(parts)


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


__all__ = [
    "ChangedFileCandidate",
    "ScanResult",
    "ScanSkippedFile",
    "ScannedFinding",
    "create_findings",
    "orchestrate_scan",
    "scan_analysis",
    "scan_changed_files",
]
