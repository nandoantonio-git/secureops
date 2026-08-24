Implemented T055 in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:121).

What changed:
- Gate decisions are now computed during analysis creation and persisted with the analysis snapshot.
- `GET /analyses/{analysisId}/gate-decision` now returns cached decisions, falls back to persisted decisions, and can build/persist a missing decision from persisted analysis data.
- The endpoint remains wired to the `GateDecision` response schema.

Verified:
- `python -m py_compile secureops/app/api/analyses.py`
- `python -m py_compile secureops/app/api/gate.py`
- `bash scripts/gate.sh secureops/app/api/analyses.py secureops/app/api/gate.py`
- `bash scripts/gate.sh`
- `pytest -q tests/unit/test_gate_eligibility.py tests/integration/test_gate_api.py`
- SQLite persistence smoke: created analysis, cleared memory cache, loaded persisted gate decision successfully.

No commit made.