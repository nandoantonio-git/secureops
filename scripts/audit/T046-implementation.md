Implemented T046 in [comments.py](/workspaces/sec-project/secureops/app/github/comments.py).

The PR feedback formatter now surfaces language coverage asymmetry explicitly, including primary/secondary role, coverage depth, data-flow support, scoped limitations, and a “not parity with Python data-flow” note for secondary-language coverage. It also handles profile-only coverage data and deduplicates/redacts limitation text.

Verification passed:

- `python -m py_compile secureops/app/github/comments.py`
- `bash scripts/gate.sh secureops/app/github/comments.py`
- `PYTHONPATH=secureops pytest secureops/tests/unit/test_pr_feedback_redaction.py secureops/tests/integration/test_language_coverage.py secureops/tests/validation/test_language_depth.py`
- `bash scripts/gate.sh`

No commit was made.