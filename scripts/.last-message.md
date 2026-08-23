Implemented T041 by adding [test_language_depth.py](/workspaces/sec-project/secureops/tests/validation/test_language_depth.py:1).

It covers:
- Quickstart Scenario 2: Python tainted SQL data-flow finding with deterministic rule and data-flow evidence.
- Quickstart Scenario 3: JavaScript secondary-language deterministic coverage, explicit limitations, and no parity claim in PR feedback.

Verification:
- `python -m py_compile secureops/tests/validation/test_language_depth.py` passed
- `bash scripts/gate.sh secureops/tests/validation/test_language_depth.py` passed
- `bash scripts/gate.sh` passed
- Targeted pytest is red as intended for TDD: Scenario 2 currently has `findings_count == 0`, and Scenario 3 lacks `language_coverage_results`. These are expected implementation gaps for the later US2 tasks.