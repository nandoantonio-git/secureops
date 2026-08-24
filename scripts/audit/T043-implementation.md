Implemented T043 in [secondary.py](/workspaces/sec-project/secureops/app/engine/rules/secondary.py).

What changed:
- Kept existing `innerHTML` / `outerHTML` DOM XSS assignment detection.
- Added deterministic JavaScript coverage for:
  - `insertAdjacentHTML`
  - `document.write` / `document.writeln`
  - `eval`
  - `Function` constructor
  - string-code `setTimeout` / `setInterval`
- Preserved the existing finding shape and source enum.

Verification passed:
- `python -m py_compile secureops/app/engine/rules/secondary.py`
- `pytest secureops/tests/unit/test_secondary_rules.py`
- `pytest secureops/tests/unit`
- `bash scripts/gate.sh secureops/app/engine/rules/secondary.py`
- `bash scripts/gate.sh`

No commit made.