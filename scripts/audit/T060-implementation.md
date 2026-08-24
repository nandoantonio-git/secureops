Implemented T060 in [finding.py](/workspaces/sec-project/secureops/app/models/finding.py): added `InvalidFindingStatusTransition`, the lifecycle transition table, `validate_finding_status_transition`, and exports.

Verification passed:
- `python -m py_compile secureops/app/models/finding.py`
- `pytest secureops/tests/unit/test_finding_lifecycle.py` - 25 passed
- `bash scripts/gate.sh secureops/app/models/finding.py`
- `bash scripts/gate.sh`

No commit was made.