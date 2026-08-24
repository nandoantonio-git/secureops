"""Unit tests for finding lifecycle transition validation."""

from __future__ import annotations

import pytest

from app.models.enums import FindingStatus
from app.models.finding import (
    InvalidFindingStatusTransition,
    validate_finding_status_transition,
)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (FindingStatus.OPEN, FindingStatus.IN_INVESTIGATION),
        (FindingStatus.OPEN, FindingStatus.RESOLVED),
        (FindingStatus.OPEN, FindingStatus.FALSE_POSITIVE),
        (FindingStatus.OPEN, FindingStatus.ACCEPTED_RISK),
        (FindingStatus.IN_INVESTIGATION, FindingStatus.OPEN),
        (FindingStatus.IN_INVESTIGATION, FindingStatus.RESOLVED),
        (FindingStatus.IN_INVESTIGATION, FindingStatus.FALSE_POSITIVE),
        (FindingStatus.IN_INVESTIGATION, FindingStatus.ACCEPTED_RISK),
        (FindingStatus.RESOLVED, FindingStatus.OPEN),
        (FindingStatus.FALSE_POSITIVE, FindingStatus.OPEN),
        (FindingStatus.ACCEPTED_RISK, FindingStatus.OPEN),
    ],
)
def test_valid_finding_lifecycle_transitions_are_allowed(
    from_status: FindingStatus,
    to_status: FindingStatus,
) -> None:
    validate_finding_status_transition(from_status, to_status)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (FindingStatus.OPEN, FindingStatus.OPEN),
        (FindingStatus.IN_INVESTIGATION, FindingStatus.IN_INVESTIGATION),
        (FindingStatus.RESOLVED, FindingStatus.RESOLVED),
        (FindingStatus.FALSE_POSITIVE, FindingStatus.FALSE_POSITIVE),
        (FindingStatus.ACCEPTED_RISK, FindingStatus.ACCEPTED_RISK),
        (FindingStatus.RESOLVED, FindingStatus.IN_INVESTIGATION),
        (FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE),
        (FindingStatus.RESOLVED, FindingStatus.ACCEPTED_RISK),
        (FindingStatus.FALSE_POSITIVE, FindingStatus.IN_INVESTIGATION),
        (FindingStatus.FALSE_POSITIVE, FindingStatus.RESOLVED),
        (FindingStatus.FALSE_POSITIVE, FindingStatus.ACCEPTED_RISK),
        (FindingStatus.ACCEPTED_RISK, FindingStatus.IN_INVESTIGATION),
        (FindingStatus.ACCEPTED_RISK, FindingStatus.RESOLVED),
        (FindingStatus.ACCEPTED_RISK, FindingStatus.FALSE_POSITIVE),
    ],
)
def test_invalid_finding_lifecycle_transitions_are_rejected(
    from_status: FindingStatus,
    to_status: FindingStatus,
) -> None:
    with pytest.raises(InvalidFindingStatusTransition) as exc_info:
        validate_finding_status_transition(from_status, to_status)

    assert str(from_status) in str(exc_info.value)
    assert str(to_status) in str(exc_info.value)
