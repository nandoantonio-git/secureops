Implemented T015 in [secureops/app/api/errors.py](/workspaces/sec-project/secureops/app/api/errors.py).

Added:
- Redaction helper for secrets, tokens, credentials, DB URLs, auth headers, and private keys
- Public API error payload types
- Domain error classes for invalid request, not found, conflict, analysis failure, dependency unavailable, and internal errors
- FastAPI response/handler registration helpers with deferred FastAPI imports

Verification passed:
- `python3 -m py_compile secureops/app/api/errors.py`
- `bash scripts/gate.sh secureops/app/api/errors.py`
- `bash scripts/gate.sh`
- Redaction smoke test

Note: the container does not have a `python` executable, so the literal `python -m py_compile ...` command cannot run here; the project gate uses `python3`, and that passed.