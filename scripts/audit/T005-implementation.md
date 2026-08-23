Implemented T005 by adding [secureops/.env.example](/workspaces/sec-project/secureops/.env.example:1) with local defaults for PostgreSQL, `advisory` gate mode, `javascript` as the secondary language, and Ollama fallback settings.

Verification passed:

```bash
bash scripts/gate.sh secureops/.env.example
# OK: gate passou (nenhum .py para checar)
```