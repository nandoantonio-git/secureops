Implemented T028 in [scan.py](/workspaces/sec-project/secureops/app/engine/scan.py:1).

What changed:
- Added changed-file scan orchestration.
- Parses changed files through the existing parser adapter.
- Runs deterministic Python rules.
- Creates ORM `Finding` objects with open status and stable fingerprints.
- Returns structured scan metadata for later remediation/API integration.

Verification passed:
- `python -m py_compile secureops/app/engine/scan.py`
- `python3 -m py_compile secureops/app/engine/scan.py`
- `bash scripts/gate.sh secureops/app/engine/scan.py`
- `bash scripts/gate.sh`

No commit was made.