Implemented T057 by adding [test_finding_lifecycle.py](/workspaces/sec-project/secureops/tests/unit/test_finding_lifecycle.py) with parameterized tests for valid and invalid `FindingStatus` transitions.

Verification:
- `python -m py_compile secureops/tests/unit/test_finding_lifecycle.py` passed
- `bash scripts/gate.sh secureops/tests/unit/test_finding_lifecycle.py` passed
- `bash scripts/gate.sh` passed
- `pytest secureops/tests/unit/test_finding_lifecycle.py` fails as expected for TDD because `InvalidFindingStatusTransition` / `validate_finding_status_transition` are not implemented yet in T060

No commit was made.