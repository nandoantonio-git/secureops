"""Stable finding fingerprint helpers.

Fingerprints identify the same finding across repeated analyses without tying
the value to database IDs, timestamps, or analysis runs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

FINGERPRINT_VERSION = "secureops-finding-v1"
FINGERPRINT_LENGTH = 64


@dataclass(frozen=True)
class FindingFingerprintInput:
    """Stable fields used to identify a finding across scans."""

    repository: str
    file_path: str
    language: str
    rule_id: str
    category: str
    source: str | None = None
    stable_anchor: str | None = None
    evidence: str | None = None
    line_start: int | None = None
    line_end: int | None = None


def build_finding_fingerprint(
    *,
    repository: str,
    file_path: str,
    language: str,
    rule_id: str,
    category: str,
    source: str | None = None,
    stable_anchor: str | None = None,
    evidence: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
) -> str:
    """Return a deterministic SHA-256 fingerprint for a finding.

    Prefer passing ``stable_anchor`` when a rule can provide a semantic anchor
    such as a symbol name, sink name, or normalized code slice. When no anchor is
    available, the helper falls back to normalized evidence and finally to the
    location range.
    """

    identity = FindingFingerprintInput(
        repository=repository,
        file_path=file_path,
        language=language,
        rule_id=rule_id,
        category=category,
        source=source,
        stable_anchor=stable_anchor,
        evidence=evidence,
        line_start=line_start,
        line_end=line_end,
    )
    return fingerprint_input(identity)


def fingerprint_input(finding: FindingFingerprintInput) -> str:
    """Return a deterministic SHA-256 fingerprint for structured input."""

    payload = {
        "version": FINGERPRINT_VERSION,
        "repository": _normalize_text(finding.repository, case_insensitive=True),
        "file_path": _normalize_path(finding.file_path),
        "language": _normalize_text(finding.language, case_insensitive=True),
        "rule_id": _normalize_text(finding.rule_id, case_insensitive=True),
        "category": _normalize_text(finding.category, case_insensitive=True),
        "source": _normalize_optional(finding.source, case_insensitive=True),
        "anchor": _identity_anchor(
            stable_anchor=finding.stable_anchor,
            evidence=finding.evidence,
            line_start=finding.line_start,
            line_end=finding.line_end,
        ),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:FINGERPRINT_LENGTH]


def fingerprint_finding(
    finding: Any,
    *,
    stable_anchor: str | None = None,
    evidence: str | None = None,
) -> str:
    """Return a fingerprint for a mapping, dataclass, Pydantic model, or ORM object."""

    return build_finding_fingerprint(
        repository=_required_field(finding, "repository"),
        file_path=_required_field(finding, "file_path"),
        language=_required_field(finding, "language"),
        rule_id=_required_field(finding, "rule_id"),
        category=_required_field(finding, "category"),
        source=_optional_field(finding, "source"),
        stable_anchor=stable_anchor or _optional_field(finding, "stable_anchor"),
        evidence=evidence or _optional_field(finding, "evidence"),
        line_start=_optional_int_field(finding, "line_start"),
        line_end=_optional_int_field(finding, "line_end"),
    )


generate_finding_fingerprint = build_finding_fingerprint


def _identity_anchor(
    *,
    stable_anchor: str | None,
    evidence: str | None,
    line_start: int | None,
    line_end: int | None,
) -> dict[str, str | int | None]:
    anchor = _normalize_optional(stable_anchor)
    if anchor is not None:
        return {"kind": "stable_anchor", "value": anchor}

    normalized_evidence = _normalize_optional(evidence)
    if normalized_evidence is not None:
        return {"kind": "evidence", "value": normalized_evidence}

    return {
        "kind": "location",
        "line_start": _normalize_line(line_start),
        "line_end": _normalize_line(line_end),
    }


def _normalize_path(file_path: str) -> str:
    path = str(file_path).strip().replace("\\", "/")
    if not path:
        raise ValueError("Fingerprint field 'file_path' cannot be empty.")

    parts = [
        part
        for part in PurePosixPath(path).parts
        if part not in ("", ".", "/")
    ]
    normalized = "/".join(parts)
    if normalized.startswith("../") or normalized == "..":
        return normalized
    return normalized.removeprefix("./")


def _normalize_text(value: Any, *, case_insensitive: bool = False) -> str:
    normalized = _normalize_optional(value, case_insensitive=case_insensitive)
    if normalized is None:
        raise ValueError("Required fingerprint fields cannot be empty.")
    return normalized


def _normalize_optional(
    value: Any,
    *,
    case_insensitive: bool = False,
) -> str | None:
    if value is None:
        return None

    if hasattr(value, "value"):
        value = value.value

    text = re.sub(r"\s+", " ", str(value).strip())
    if not text:
        return None
    if case_insensitive:
        return text.casefold()
    return text


def _normalize_line(value: int | None) -> int | None:
    if value is None:
        return None
    line = int(value)
    if line < 1:
        raise ValueError("Fingerprint line values must be one-based positive integers.")
    return line


def _required_field(finding: Any, name: str) -> str:
    value = _field_value(finding, name)
    if value is None:
        raise ValueError(f"Missing required fingerprint field '{name}'.")
    return str(value)


def _optional_field(finding: Any, name: str) -> Any:
    return _field_value(finding, name)


def _optional_int_field(finding: Any, name: str) -> int | None:
    value = _field_value(finding, name)
    if value is None:
        return None
    return int(value)


def _field_value(finding: Any, name: str) -> Any:
    if isinstance(finding, dict):
        return finding.get(name)
    return getattr(finding, name, None)


__all__ = [
    "FINGERPRINT_LENGTH",
    "FINGERPRINT_VERSION",
    "FindingFingerprintInput",
    "build_finding_fingerprint",
    "fingerprint_finding",
    "fingerprint_input",
    "generate_finding_fingerprint",
]
