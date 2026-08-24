Implemented and verified T053.

Gate behavior is in [gate.py](/workspaces/sec-project/secureops/app/api/gate.py:17): advisory mode returns `advisory_only`, and blocking mode only blocks open critical findings with at least two distinct deterministic non-AI evidence signals. The gate endpoint is wired through [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:151) with the `GateDecision` response schema and `getGateDecision` operation id.

Verification passed:
- `python -m py_compile secureops/app/api/gate.py`
- `pytest secureops/tests/unit/test_gate_eligibility.py`
- `pytest secureops/tests/integration/test_gate_api.py`
- `pytest secureops/tests/integration/test_openapi_contract.py -k gate_decision`
- `bash scripts/gate.sh secureops/app/api/gate.py secureops/app/api/analyses.py`
- `bash scripts/gate.sh`

No commit was made.