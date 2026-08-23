Implemented T016 by adding [parser.py](/workspaces/sec-project/secureops/app/engine/parser.py:1).

It now provides a Tree-sitter adapter for:
- Python: `.py`, `.pyw`
- JavaScript secondary language: `.js`, `.jsx`, `.mjs`, `.cjs`

Included helpers for language normalization/detection, parsing files/source strings, walking nodes, extracting node text, line ranges, and clear parser/unsupported-language errors. Tree-sitter imports are deferred until parsing so module import and compile remain stable.

Verification passed:
- `python3 -m py_compile secureops/app/engine/parser.py`
- `bash scripts/gate.sh secureops/app/engine/parser.py`
- `bash scripts/gate.sh`
- parser helper smoke check

Note: this container has no `python` executable on PATH, so I used `python3`, matching `scripts/gate.sh`. No commit was made.