"""Scan orchestration for changed pull request files."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from app.engine.fingerprint import build_finding_fingerprint
from app.engine.fingerprint import fingerprint_finding
from app.engine.fingerprint import normalize_finding_anchor
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
from app.engine.rules.secondary import (
    SecondaryRuleFinding,
    detect_secondary_vulnerabilities_from_source,
)
from app.engine.taint import detect_python_taint_flows_from_source
from app.models.enums import FindingSource, FindingStatus, SignalType
from app.remediation.templates import select_template

if TYPE_CHECKING:
    from app.models.finding import DetectionSignal
    from app.models.finding import Finding

RuleFinding = Union[PythonRuleFinding, SecondaryRuleFinding]


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
    *,
    previous_findings: Iterable[Any] | None = None,
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

    if previous_findings is not None:
        preserve_overridden_findings(findings, previous_findings)

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
    *,
    previous_findings: Iterable[Any] | None = None,
) -> list[Finding]:
    """Return ORM findings created from changed files."""

    return orchestrate_scan(
        analysis_id,
        repository,
        changed_files,
        previous_findings=previous_findings,
    ).findings


def create_findings(
    analysis_id: str,
    repository: str,
    changed_files: Iterable[Any],
    *,
    previous_findings: Iterable[Any] | None = None,
) -> list[Finding]:
    """Compatibility wrapper for callers that only need finding objects."""

    return scan_changed_files(
        analysis_id,
        repository,
        changed_files,
        previous_findings=previous_findings,
    )


def scan_analysis(analysis: Any, changed_files: Iterable[Any]) -> ScanResult:
    """Run a scan for an analysis ORM object and attach created findings."""

    previous_findings = list(getattr(analysis, "findings", []))
    result = orchestrate_scan(
        str(analysis.id),
        str(analysis.repository),
        changed_files,
        previous_findings=previous_findings,
    )
    analysis.findings.extend(result.findings)
    return result


def preserve_overridden_findings(
    findings: list[Finding],
    previous_findings: Iterable[Any],
) -> list[Finding]:
    """Carry forward manual override state onto same-fingerprint findings."""

    overridden_by_fingerprint = _overridden_findings_by_fingerprint(previous_findings)
    for finding in findings:
        fingerprint = _fingerprint_for_existing_finding(finding)
        if fingerprint is None:
            continue

        overridden_finding = overridden_by_fingerprint.get(fingerprint)
        if overridden_finding is None:
            continue

        _copy_override_state(finding, overridden_finding)
    return findings


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
) -> list[RuleFinding]:
    if language == "python":
        rule_findings = detect_python_vulnerabilities_from_source(
            source_text,
            file_path=file_path,
        )
        return [
            *rule_findings,
            *detect_python_taint_flows_from_source(source_text, file_path=file_path),
        ]
    if language == "javascript":
        return detect_secondary_vulnerabilities_from_source(
            source_text,
            file_path=file_path,
            language=language,
        )
    return []


def _create_scanned_finding(
    *,
    analysis_id: str,
    repository: str,
    rule_finding: RuleFinding,
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
    finding.detection_signals.extend(_create_detection_signals(rule_finding))
    return ScannedFinding(
        finding=finding,
        evidence=rule_finding.evidence,
        stable_anchor=stable_anchor,
        sink=rule_finding.sink,
        user_input=rule_finding.user_input,
    )


def _create_detection_signals(rule_finding: RuleFinding) -> list[DetectionSignal]:
    from app.models.finding import DetectionSignal

    signals = [
        DetectionSignal(
            signal_type=SignalType.DETERMINISTIC_RULE,
            deterministic=True,
            summary=f"Deterministic rule {rule_finding.rule_id} matched.",
        ),
    ]
    if rule_finding.source == FindingSource.PRIMARY_LANGUAGE_TAINT:
        signals.append(
            DetectionSignal(
                signal_type=SignalType.DATA_FLOW,
                deterministic=True,
                summary=_data_flow_signal_summary(rule_finding),
            ),
        )

    template_id = _matching_template_id(rule_finding)
    if template_id is not None:
        signals.append(
            DetectionSignal(
                signal_type=SignalType.TEMPLATE_MATCH,
                deterministic=True,
                summary=(
                    f"Reviewed remediation template {template_id} matched "
                    f"{rule_finding.rule_id}."
                ),
            ),
        )

    if _include_ai_assisted_classification(rule_finding):
        signals.append(
            DetectionSignal(
                signal_type=SignalType.AI_ASSISTED_CLASSIFICATION,
                deterministic=False,
                summary=(
                    "AI-assisted classification may enrich review context "
                    f"for {rule_finding.rule_id}."
                ),
            ),
        )

    return signals


def _data_flow_signal_summary(rule_finding: RuleFinding) -> str:
    source = rule_finding.user_input or "untrusted input"
    return f"Data flow from {source} to {rule_finding.sink} matched."


def _matching_template_id(rule_finding: RuleFinding) -> str | None:
    template = select_template(
        rule_id=rule_finding.rule_id,
        category=rule_finding.category,
        language=rule_finding.language,
    )
    if template is None:
        return None
    return template.template_id


def _include_ai_assisted_classification(rule_finding: RuleFinding) -> bool:
    return rule_finding.source != FindingSource.PRIMARY_LANGUAGE_TAINT


def _stable_anchor(rule_finding: RuleFinding) -> str:
    anchor_value = rule_finding.user_input or rule_finding.evidence
    anchor = normalize_finding_anchor(
        rule_finding.rule_id,
        rule_finding.source,
        rule_finding.sink,
        anchor_value,
    )
    if anchor is not None:
        return anchor

    return rule_finding.rule_id


def _overridden_findings_by_fingerprint(
    previous_findings: Iterable[Any],
) -> dict[str, Any]:
    overridden_findings: dict[str, Any] = {}
    for finding in previous_findings:
        if not _has_override_history(finding):
            continue

        fingerprint = _fingerprint_for_existing_finding(finding)
        if fingerprint is None:
            continue

        overridden_findings[fingerprint] = finding
    return overridden_findings


def _has_override_history(finding: Any) -> bool:
    return bool(_field(finding, "history", []))


def _fingerprint_for_existing_finding(finding: Any) -> str | None:
    fingerprint = _field(finding, "fingerprint")
    if fingerprint:
        return str(fingerprint)

    try:
        return fingerprint_finding(finding)
    except (TypeError, ValueError):
        return None


def _copy_override_state(finding: Any, overridden_finding: Any) -> None:
    status = _field(overridden_finding, "status")
    if status is not None:
        _set_field(finding, "status", status)

    severity = _field(overridden_finding, "severity")
    if severity is not None:
        _set_field(finding, "severity", severity)

    _replace_history(finding, _field(overridden_finding, "history", []))


def _replace_history(finding: Any, source_history: Iterable[Any]) -> None:
    history_entries = list(source_history)
    if isinstance(finding, dict):
        finding["history"] = [
            _history_entry_mapping(entry)
            for entry in history_entries
        ]
        return

    target_history = _field(finding, "history")
    if target_history is None:
        return

    target_history.clear()
    target_history.extend(_clone_history_entries(history_entries))


def _history_entry_mapping(entry: Any) -> dict[str, Any]:
    if isinstance(entry, dict):
        return dict(entry)
    return {
        "changed_by": _field(entry, "changed_by"),
        "change_type": _field(entry, "change_type"),
        "from_value": _field(entry, "from_value"),
        "to_value": _field(entry, "to_value"),
        "reason": _field(entry, "reason"),
        "created_at": _field(entry, "created_at"),
    }


def _clone_history_entries(history_entries: Iterable[Any]) -> list[Any]:
    from app.models.finding import FindingHistoryEntry

    cloned_entries = []
    for entry in history_entries:
        kwargs = {
            "changed_by": _field(entry, "changed_by"),
            "change_type": _field(entry, "change_type"),
            "from_value": _field(entry, "from_value"),
            "to_value": _field(entry, "to_value"),
            "reason": _field(entry, "reason"),
        }
        created_at = _field(entry, "created_at")
        if created_at is not None:
            kwargs["created_at"] = created_at
        cloned_entries.append(FindingHistoryEntry(**kwargs))
    return cloned_entries


def _set_field(value: Any, name: str, field_value: Any) -> None:
    if isinstance(value, dict):
        value[name] = field_value
        return
    setattr(value, name, field_value)


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


__all__ = [
    "ChangedFileCandidate",
    "ScanResult",
    "ScanSkippedFile",
    "ScannedFinding",
    "create_findings",
    "orchestrate_scan",
    "preserve_overridden_findings",
    "scan_analysis",
    "scan_changed_files",
]
