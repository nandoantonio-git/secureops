Implemented T047 in [secureops/README.md](/workspaces/sec-project/secureops/README.md).

Added US2 documentation for the two-language support model, JavaScript as the secondary `minimal_deterministic` language, the supported `javascript.dom.inner_html` rule, and known limitations including no JavaScript data-flow parity with Python.

Verification passed:

```bash
bash scripts/gate.sh secureops/README.md
```

No commit was made.