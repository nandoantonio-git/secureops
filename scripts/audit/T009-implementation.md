Implemented T009 in [secureops/app/config.py](/workspaces/sec-project/secureops/app/config.py:1).

Added Pydantic settings for:
- `DATABASE_URL`
- `SECONDARY_LANGUAGE`
- `GATE_MODE`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_FALLBACK_ENABLED`

Also added validation, normalization, `.env` loading, and cached `get_settings()`.

Verification:
- `python -m py_compile secureops/app/config.py`: could not run because this container has no `python` binary.
- `python3 -m py_compile secureops/app/config.py`: passed.
- `bash scripts/gate.sh secureops/app/config.py`: passed.
- `bash scripts/gate.sh`: passed.

No commit was made.