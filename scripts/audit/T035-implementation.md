Implemented T035 in [secureops/app/github/comments.py](/workspaces/sec-project/secureops/app/github/comments.py:1).

What changed:
- Added `format_pr_feedback(findings=..., mode=...)` for structured GitHub PR Markdown feedback.
- Includes required sections: Cause, Evidence, Impact, Recommended correction, Safe example.
- Redacts secrets/tokens/credentials/database URL userinfo/private key material while preserving actionable context like file, line, variable names, header names, URL host/path, and key type.

Verification passed:
- `python -m py_compile secureops/app/github/comments.py`
- `pytest secureops/tests/unit/test_pr_feedback_redaction.py` -> 5 passed
- `bash scripts/gate.sh secureops/app/github/comments.py`
- `bash scripts/gate.sh`

No commit was made.