"""GitHub commit status and check-run payload helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

CHECK_NAME = "SecureOps gate"
STATUS_CONTEXT = "secureops/gate"

_ADVISORY_DECISIONS = {"advisory", "advisory_only"}
_PASSED_DECISIONS = {"passed"}
_BLOCKED_DECISIONS = {"blocked"}
_DESCRIPTION_LIMIT = 140


def build_commit_status(
    gate_decision: Any,
    *,
    target_url: str | None = None,
    context: str = STATUS_CONTEXT,
) -> dict[str, str]:
    """Return a GitHub Statuses API payload for a gate decision."""

    decision = _decision_value(gate_decision)
    payload = {
        "state": _status_state(decision),
        "description": _truncate(_summary_for_decision(decision)),
        "context": context,
    }
    if target_url:
        payload["target_url"] = target_url
    return payload


def build_check_run(
    gate_decision: Any,
    *,
    head_sha: str | None = None,
    name: str = CHECK_NAME,
    details_url: str | None = None,
) -> dict[str, Any]:
    """Return a GitHub Checks API check-run payload for a gate decision."""

    decision = _decision_value(gate_decision)
    payload: dict[str, Any] = {
        "name": name,
        "status": "completed",
        "conclusion": _check_conclusion(decision),
        "output": {
            "title": _check_title(decision),
            "summary": _summary_for_decision(decision),
            "text": _check_text(gate_decision),
        },
    }
    if head_sha:
        payload["head_sha"] = head_sha
    if details_url:
        payload["details_url"] = details_url
    return payload


def build_github_status_output(
    gate_decision: Any,
    *,
    head_sha: str | None = None,
    target_url: str | None = None,
    details_url: str | None = None,
    context: str = STATUS_CONTEXT,
    name: str = CHECK_NAME,
) -> dict[str, Any]:
    """Return both commit status and check-run payloads for GitHub publishing."""

    return {
        "commit_status": build_commit_status(
            gate_decision,
            target_url=target_url,
            context=context,
        ),
        "check_run": build_check_run(
            gate_decision,
            head_sha=head_sha,
            name=name,
            details_url=details_url,
        ),
    }


def build_status_payload(
    gate_decision: Any,
    *,
    target_url: str | None = None,
    context: str = STATUS_CONTEXT,
) -> dict[str, str]:
    """Compatibility alias for commit status payload creation."""

    return build_commit_status(
        gate_decision,
        target_url=target_url,
        context=context,
    )


def build_check_run_payload(
    gate_decision: Any,
    *,
    head_sha: str | None = None,
    name: str = CHECK_NAME,
    details_url: str | None = None,
) -> dict[str, Any]:
    """Compatibility alias for check-run payload creation."""

    return build_check_run(
        gate_decision,
        head_sha=head_sha,
        name=name,
        details_url=details_url,
    )


def _status_state(decision: str) -> str:
    if decision in _BLOCKED_DECISIONS:
        return "failure"
    return "success"


def _check_conclusion(decision: str) -> str:
    if decision in _BLOCKED_DECISIONS:
        return "failure"
    if decision in _ADVISORY_DECISIONS:
        return "neutral"
    return "success"


def _check_title(decision: str) -> str:
    if decision in _BLOCKED_DECISIONS:
        return "SecureOps blocked this pull request"
    if decision in _PASSED_DECISIONS:
        return "SecureOps gate passed"
    if decision in _ADVISORY_DECISIONS:
        return "SecureOps advisory review completed"
    return "SecureOps gate decision completed"


def _summary_for_decision(decision: str) -> str:
    if decision in _BLOCKED_DECISIONS:
        return "Blocked: critical deterministic security findings require action."
    if decision in _PASSED_DECISIONS:
        return "Passed: no blocking security findings were detected."
    if decision in _ADVISORY_DECISIONS:
        return "Advisory: findings were reported without blocking merge."
    return "SecureOps completed with an unrecognized gate decision."


def _check_text(gate_decision: Any) -> str:
    reasons = _as_text_list(_field(gate_decision, "reasons", []))
    blocking_findings = _as_text_list(
        _field(
            gate_decision,
            "blocking_findings",
            _field(gate_decision, "blocking_finding_ids", []),
        ),
    )

    lines = ["### Gate decision", ""]
    lines.append(f"- Mode: `{_field_text(gate_decision, 'mode', 'unknown')}`")
    lines.append(f"- Decision: `{_field_text(gate_decision, 'decision', 'unknown')}`")

    if reasons:
        lines.extend(["", "### Reasons"])
        lines.extend(f"- {reason}" for reason in reasons)

    if blocking_findings:
        lines.extend(["", "### Blocking findings"])
        lines.extend(f"- `{finding_id}`" for finding_id in blocking_findings)

    return "\n".join(lines)


def _decision_value(gate_decision: Any) -> str:
    return _field_text(gate_decision, "decision", "unknown").lower()


def _field_text(item: Any, name: str, default: str) -> str:
    return _as_text(_field(item, name, default), default=default)


def _field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    return getattr(item, name, default)


def _as_text_list(value: Any) -> list[str]:
    return [_as_text(item) for item in _as_sequence(value) if _as_text(item)]


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return value
    return (value,)


def _as_text(value: Any, *, default: str = "") -> str:
    if value is None:
        return default

    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        value = enum_value

    text = str(value)
    return text if text.strip() else default


def _truncate(value: str, limit: int = _DESCRIPTION_LIMIT) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3].rstrip()}..."


__all__ = [
    "CHECK_NAME",
    "STATUS_CONTEXT",
    "build_check_run",
    "build_check_run_payload",
    "build_commit_status",
    "build_github_status_output",
    "build_status_payload",
]
