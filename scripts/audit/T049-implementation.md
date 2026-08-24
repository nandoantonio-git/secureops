Added [test_gate_api.py](/workspaces/sec-project/secureops/tests/integration/test_gate_api.py) with integration coverage for `/analyses/{analysisId}/gate-decision` in both `advisory` and `blocking_enabled` modes.

Verification:
- `python -m py_compile secureops/tests/integration/test_gate_api.py` passed
- `bash scripts/gate.sh secureops/tests/integration/test_gate_api.py` passed
- `pytest secureops/tests/integration/test_gate_api.py -q` is red as expected for TDD: blocking mode currently returns `passed` instead of expected `blocked`, pending T053 gate implementation.