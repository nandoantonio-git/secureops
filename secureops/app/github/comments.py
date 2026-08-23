"""GitHub Pull Request comment formatting helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED_VALUE = "[REDACTED]"

_PRIVATE_KEY_BLOCK_PATTERN = re.compile(
    r"(-----BEGIN (?P<kind>[A-Z ]*PRIVATE KEY)-----)"
    r".*?"
    r"(-----END (?P=kind)-----)",
    re.DOTALL,
)
_DATABASE_URL_PATTERN = re.compile(
    r"(?P<scheme>\b(?:postgresql|postgres|mysql|mariadb|mongodb|redis)://)"
    r"(?P<userinfo>[^\s'\"/]+)@"
    r"(?P<location>[A-Za-z0-9.-]+(?::\d+)?(?:/[^\s'\"),}]*)?)",
    re.IGNORECASE,
)
_AUTHORIZATION_PATTERN = re.compile(
    r"(?P<prefix>\bAuthorization\b['\"]?\s*[:=]\s*['\"]?"
    r"(?:Bearer|Basic)\s+)"
    r"(?P<credential>[A-Za-z0-9._~+/=-]{8,})",
    re.IGNORECASE,
)
_AUTH_TUPLE_PATTERN = re.compile(
    r"(?P<prefix>\bauth\s*=\s*\(\s*['\"][^'\"]+['\"]\s*,\s*['\"])"
    r"(?P<credential>[^'\"]+)"
    r"(?P<suffix>['\"]\s*\))",
    re.IGNORECASE,
)
_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<prefix>\b[\w.-]*(?:api[_-]?key|private[_-]?key|password|passwd|pwd|"
    r"secret|token|credential)[\w.-]*\b\s*[:=]\s*)"
    r"(?P<quote>['\"])(?P<credential>[^'\"]{4,})(?P=quote)",
    re.IGNORECASE,
)
_DIRECT_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def format_pr_feedback(
    *,
    findings: Sequence[Any],
    mode: str = "advisory",
) -> str:
    """Return structured, redacted Markdown feedback for a GitHub PR."""

    normalized_mode = _as_text(mode, default="advisory")
    finding_count = len(findings)
    plural = "" if finding_count == 1 else "s"
    lines = [
        "## SecureOps PR feedback",
        "",
        f"Mode: `{normalized_mode}`",
        f"Findings: {finding_count} open item{plural}",
    ]

    if finding_count == 0:
        lines.extend(["", "No actionable security findings were detected."])
        return "\n".join(lines)

    for index, finding in enumerate(findings, start=1):
        remediation = _get(finding, "remediation", default={})
        location = _format_location(finding)
        severity = _as_text(_get(finding, "severity"), default="unknown")
        rule_id = _as_text(_get(finding, "rule_id"), default="unknown_rule")
        category = _as_text(_get(finding, "category"), default="")

        heading = f"### Finding {index}: {severity} - `{rule_id}`"
        if category:
            heading = f"{heading} ({category})"

        lines.extend(
            [
                "",
                heading,
                f"- Location: {location}",
                f"- Status: {_as_text(_get(finding, 'status'), default='open')}",
                f"- Source: {_as_text(_get(finding, 'source'), default='unknown')}",
                "",
                "**Cause**",
                _redact(_as_text(_get(remediation, "cause"))),
                "",
                "**Evidence**",
                _redact(_as_text(_get(remediation, "evidence"))),
                "",
                "**Impact**",
                _redact(_as_text(_get(remediation, "impact"))),
                "",
                "**Recommended correction**",
                _redact(_as_text(_get(remediation, "recommended_correction"))),
                "",
                "**Safe example**",
                _redact(_as_text(_get(remediation, "safe_example"))),
            ],
        )

    return "\n".join(lines)


def redact_sensitive_feedback(value: str) -> str:
    """Redact sensitive payloads while keeping PR feedback actionable."""

    return _redact(value)


def _redact(value: str) -> str:
    redacted = _PRIVATE_KEY_BLOCK_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}\n{REDACTED_VALUE}\n{match.group(3)}"
        ),
        value,
    )
    redacted = _DATABASE_URL_PATTERN.sub(
        lambda match: (
            f"{match.group('scheme')}{REDACTED_VALUE}@"
            f"{match.group('location')}"
        ),
        redacted,
    )
    redacted = _AUTHORIZATION_PATTERN.sub(
        lambda match: f"{match.group('prefix')}{REDACTED_VALUE}",
        redacted,
    )
    redacted = _AUTH_TUPLE_PATTERN.sub(
        lambda match: (
            f"{match.group('prefix')}{REDACTED_VALUE}{match.group('suffix')}"
        ),
        redacted,
    )
    redacted = _SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: (
            f"{match.group('prefix')}{match.group('quote')}"
            f"{REDACTED_VALUE}{match.group('quote')}"
        ),
        redacted,
    )

    for pattern in _DIRECT_SECRET_PATTERNS:
        redacted = pattern.sub(REDACTED_VALUE, redacted)

    return redacted


def _format_location(finding: Any) -> str:
    file_path = _as_text(_get(finding, "file_path"), default="unknown file")
    line_start = _get(finding, "line_start")
    line_end = _get(finding, "line_end")

    if line_start is None:
        return file_path

    location = f"{file_path}:{line_start}"
    if line_end and line_end != line_start:
        location = f"{location}-{line_end}"
    return location


def _get(value: Any, key: str, *, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _as_text(value: Any, *, default: str = "") -> str:
    if value is None:
        return default

    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        value = enum_value

    text = str(value)
    return text if text.strip() else default


__all__ = [
    "REDACTED_VALUE",
    "format_pr_feedback",
    "redact_sensitive_feedback",
]
