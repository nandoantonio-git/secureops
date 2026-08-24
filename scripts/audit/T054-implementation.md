Implemented [status.py](/workspaces/sec-project/secureops/app/github/status.py:1) with helpers for GitHub commit status and check-run payloads covering `advisory/advisory_only`, `passed`, and `blocked` decisions.

Verified:
- `python -m py_compile secureops/app/github/status.py`
- `bash scripts/gate.sh secureops/app/github/status.py`
- `bash scripts/gate.sh`

All passed. No commit made.