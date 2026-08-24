Implemented T062.

Changed:
- Added normalized anchor construction in [fingerprint.py](/workspaces/sec-project/secureops/app/engine/fingerprint.py:124).
- Added engine-level override preservation in [scan.py](/workspaces/sec-project/secureops/app/engine/scan.py:84), matching repeated findings by fingerprint and carrying forward status, severity, and history.
- Updated scan entry points to accept `previous_findings` without breaking existing callers.

Verified:
- `python -m py_compile secureops/app/engine/fingerprint.py`
- `python -m py_compile secureops/app/engine/scan.py`
- `bash scripts/gate.sh secureops/app/engine/fingerprint.py secureops/app/engine/scan.py`
- `bash scripts/gate.sh`
- `pytest secureops/tests/integration/test_finding_override_api.py secureops/tests/validation/test_manual_override_history.py -q`

All passed. No commit made.