"""Gate eligibility rules for restricted blocking mode."""

from __future__ import annotations

from typing import Any

from app.models.enums import (
    DETERMINISTIC_SIGNAL_TYPES,
    FindingStatus,
    GateDecisionStatus,
    GateMode,
    Severity,
    SignalType,
)


def build_gate_decision(
    *,
    analysis_id: str,
    mode: str | GateMode,
    findings: list[Any],
) -> dict[str, Any]:
    """Build a merge gate decision for an analysis."""

    mode_value = _value(mode)
    if mode_value == GateMode.ADVISORY.value:
        return {
            "analysis_id": analysis_id,
            "mode": mode_value,
            "decision": GateDecisionStatus.ADVISORY_ONLY.value,
            "reasons": ["Advisory mode does not block merge."],
            "blocking_findings": [],
        }

    blocking_finding_ids = [
        str(_field(finding, "id"))
        for finding in findings
        if is_finding_blocking_eligible(finding)
    ]
    if blocking_finding_ids:
        return {
            "analysis_id": analysis_id,
            "mode": mode_value,
            "decision": GateDecisionStatus.BLOCKED.value,
            "reasons": [
                "Restricted blocking found critical deterministic evidence.",
            ],
            "blocking_findings": blocking_finding_ids,
        }

    return {
        "analysis_id": analysis_id,
        "mode": mode_value,
        "decision": GateDecisionStatus.PASSED.value,
        "reasons": [
            "No critical finding met restricted deterministic blocking criteria.",
        ],
        "blocking_findings": [],
    }


def is_finding_blocking_eligible(finding: Any) -> bool:
    """Return whether a finding may block in restricted blocking mode."""

    if _value(_field(finding, "severity")) != Severity.CRITICAL.value:
        return False
    if _value(_field(finding, "status", FindingStatus.OPEN)) != (
        FindingStatus.OPEN.value
    ):
        return False

    deterministic_signal_types = {
        _value(_field(signal, "signal_type"))
        for signal in _field(finding, "detection_signals", [])
        if _field(signal, "deterministic") is True
        and _value(_field(signal, "signal_type")) in _DETERMINISTIC_SIGNAL_VALUES
    }
    return len(deterministic_signal_types) >= 2


def _field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


_DETERMINISTIC_SIGNAL_VALUES = {
    _value(signal_type)
    for signal_type in DETERMINISTIC_SIGNAL_TYPES
    if signal_type != SignalType.AI_ASSISTED_CLASSIFICATION
}
