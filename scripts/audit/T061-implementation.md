Implemented T061.

Changed:
- Added `POST /findings/{findingId}/override` in [findings.py](/workspaces/sec-project/secureops/app/api/findings.py:47)
- Added manual override application with append-only `history` entries in [findings.py](/workspaces/sec-project/secureops/app/api/findings.py:74)
- Added override carry-forward by fingerprint for newly created findings in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:99)

Verified:
- `python -m py_compile secureops/app/api/findings.py`
- `pytest secureops/tests/integration/test_finding_override_api.py -q`
- `pytest secureops/tests/validation/test_manual_override_history.py -q`
- `bash scripts/gate.sh secureops/app/api/findings.py secureops/app/api/analyses.py`
- `bash scripts/gate.sh`

All passed. No commit made.