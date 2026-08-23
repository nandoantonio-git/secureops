Implemented T017 in [fingerprint.py](/workspaces/sec-project/secureops/app/engine/fingerprint.py:1).

Added a stable SHA-256 finding fingerprint helper with:
- normalized repository, path, language, rule, category, source
- semantic `stable_anchor` support, falling back to evidence or line range
- helpers for direct args, structured dataclass input, dicts, Pydantic-style objects, and ORM objects

Verification passed:
- `python3 -m py_compile secureops/app/engine/fingerprint.py`
- `bash scripts/gate.sh secureops/app/engine/fingerprint.py`
- `bash scripts/gate.sh`
- smoke check for deterministic normalization

No commit was made. Note: this container has no `python` executable on PATH, so I used `python3`, which matches `scripts/gate.sh`.