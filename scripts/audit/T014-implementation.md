Implemented OpenAPI request/response Pydantic schemas in [schemas.py](/workspaces/sec-project/secureops/app/api/schemas.py:1), matching the contract models and reusing the existing domain enums.

Verification:
- `python3 -m py_compile secureops/app/api/schemas.py` passed
- `bash scripts/gate.sh secureops/app/api/schemas.py` passed
- `bash scripts/gate.sh` passed

Note: the literal `python -m py_compile ...` command cannot run here because `python` is not on PATH; the project gate uses `python3`, which passed. No commit was made.