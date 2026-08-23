Implemented T030 and wired enough of the analysis path for the stated validation to pass.

Changed:
- Added [ollama_client.py](/workspaces/sec-project/secureops/app/remediation/ollama_client.py:1): synchronous Ollama `/api/generate` client with timeout handling, invalid-response handling, and low-confidence fallback.
- Added [service.py](/workspaces/sec-project/secureops/app/remediation/service.py:1): remediation orchestration that falls back to reviewed templates/deterministic guidance.
- Added minimal in-memory analysis/finding/gate routes in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:1) and [findings.py](/workspaces/sec-project/secureops/app/api/findings.py:1), registered from [main.py](/workspaces/sec-project/secureops/app/main.py:1).

Verification passed:
- `python -m py_compile secureops/app/remediation/ollama_client.py`
- `pytest secureops/tests/validation/test_ollama_fallback.py` -> 1 passed
- `bash scripts/gate.sh`
- Also checked `test_advisory_python_feedback.py` with the Ollama fallback validation -> 2 passed

I did not commit changes. I also installed the project runtime/test dependencies into the user Python environment so the validation could run in this container.