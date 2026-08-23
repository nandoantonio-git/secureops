Implemented T018.

Added baseline fixtures under [secureops/tests/fixtures](/workspaces/sec-project/secureops/tests/fixtures/README.md):

- Python clean fixture
- Python vulnerable command injection fixture
- Python critical unprotected SQL data-flow fixture
- JavaScript clean fixture
- JavaScript deterministic DOM XSS fixture
- Ollama fallback fixture using unsafe YAML load
- Secondary fallback eval fixture
- README mapping quickstart fixture requirements to paths

Verification passed:

```bash
bash scripts/gate.sh <added fixture files>
```

Result: `OK: gate passou`

Also ran `git diff --check`; no whitespace issues found. No commit was made.