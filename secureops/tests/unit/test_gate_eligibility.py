"""Unit tests for deterministic gate eligibility evidence."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.api.gate import is_finding_blocking_eligible
from app.models.enums import Severity, SignalType


@dataclass(frozen=True)
class SignalForGate:
    """Minimal detection signal shape consumed by gate eligibility."""

    signal_type: SignalType
    deterministic: bool
    summary: str = "test signal"


@dataclass(frozen=True)
class FindingForGate:
    """Minimal finding shape consumed by gate eligibility."""

    severity: Severity
    detection_signals: list[SignalForGate]
    id: str = "finding-1"


def _signal(
    signal_type: SignalType,
    *,
    deterministic: bool = True,
) -> SignalForGate:
    return SignalForGate(
        signal_type=signal_type,
        deterministic=deterministic,
    )


def _finding(
    severity: Severity,
    signals: list[SignalForGate],
) -> FindingForGate:
    return FindingForGate(
        severity=severity,
        detection_signals=signals,
    )


def test_critical_finding_with_rule_and_data_flow_is_blocking_eligible() -> None:
    finding = _finding(
        Severity.CRITICAL,
        [
            _signal(SignalType.DETERMINISTIC_RULE),
            _signal(SignalType.DATA_FLOW),
        ],
    )

    assert is_finding_blocking_eligible(finding) is True


def test_critical_finding_with_multiple_deterministic_signals_is_eligible() -> None:
    finding = _finding(
        Severity.CRITICAL,
        [
            _signal(SignalType.DETERMINISTIC_RULE),
            _signal(SignalType.TEMPLATE_MATCH),
        ],
    )

    assert is_finding_blocking_eligible(finding) is True


@pytest.mark.parametrize(
    ("severity", "signals"),
    [
        (
            Severity.HIGH,
            [
                _signal(SignalType.DETERMINISTIC_RULE),
                _signal(SignalType.DATA_FLOW),
            ],
        ),
        (
            Severity.CRITICAL,
            [
                _signal(SignalType.DETERMINISTIC_RULE),
            ],
        ),
        (
            Severity.CRITICAL,
            [
                _signal(SignalType.DETERMINISTIC_RULE),
                _signal(SignalType.AI_ASSISTED_CLASSIFICATION),
            ],
        ),
        (
            Severity.CRITICAL,
            [
                _signal(SignalType.DETERMINISTIC_RULE),
                _signal(SignalType.DATA_FLOW, deterministic=False),
            ],
        ),
        (
            Severity.CRITICAL,
            [
                _signal(SignalType.AI_ASSISTED_CLASSIFICATION),
                _signal(SignalType.AI_ASSISTED_CLASSIFICATION),
            ],
        ),
    ],
)
def test_finding_without_critical_deterministic_evidence_is_not_eligible(
    severity: Severity,
    signals: list[SignalForGate],
) -> None:
    finding = _finding(severity, signals)

    assert is_finding_blocking_eligible(finding) is False
