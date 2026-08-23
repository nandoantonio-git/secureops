Implemented T006 by adding controlled fixture directories under [secureops/tests/fixtures](/workspaces/sec-project/secureops/tests/fixtures/.gitkeep):

- `python_clean/`
- `python_vulnerable/`
- `python_fallback/`
- `secondary_clean/`
- `secondary_vulnerable/`
- `secondary_fallback/`

Each directory has a `.gitkeep` so it is tracked.

Verification passed:

```bash
bash scripts/gate.sh secureops/tests/fixtures/python_clean/.gitkeep secureops/tests/fixtures/python_vulnerable/.gitkeep secureops/tests/fixtures/python_fallback/.gitkeep secureops/tests/fixtures/secondary_clean/.gitkeep secureops/tests/fixtures/secondary_vulnerable/.gitkeep secureops/tests/fixtures/secondary_fallback/.gitkeep
```

Result: `OK: gate passou (nenhum .py para checar)`

No commit was made.