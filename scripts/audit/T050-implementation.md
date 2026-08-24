Implemented T050.

Added the Scenario 4 validation test in [test_restricted_blocking.py](/workspaces/sec-project/secureops/tests/validation/test_restricted_blocking.py:1). Per TDD note, it failed first because the gate returned `passed` instead of `blocked`.

Then added restricted blocking gate logic in [gate.py](/workspaces/sec-project/secureops/app/api/gate.py:1) and wired `/gate-decision` in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:155). Blocking now requires an open critical finding with at least two deterministic non-AI signal types.

Verification passed:
- `pytest secureops/tests/validation/test_restricted_blocking.py -q`
- `pytest secureops/tests/unit/test_gate_eligibility.py secureops/tests/integration/test_gate_api.py -q`
- `python -m py_compile secureops/tests/validation/test_restricted_blocking.py`
- `bash scripts/gate.sh secureops/tests/validation/test_restricted_blocking.py`
- `bash scripts/gate.sh`

No commit was made.