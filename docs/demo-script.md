# Demo script (FIAP checkpoint / technical defense)

~8–10 minutes. Every command below was actually run and verified working
during development (see commit history) — nothing here is aspirational.

## 0. Before you're in the room

```bash
docker compose up --build   # from the repo root
```

Wait for `docker compose ps` to show `db` healthy and `api`/`frontend`
running. Open the dashboard at `http://localhost:8080` once — confirms
`VITE_DASHBOARD_REPOSITORY=secureops` in `docker-compose.yml` matches
whatever repository name you use in step 2 below.

## 1. What this is (30s)

"SecureOps is a PR-first vulnerability feedback service — a PR's changed
files go in, structured findings with cause/evidence/impact/fix come out,
plus a gate decision. No queue, no async job: analysis happens inline in
the request." Point at `docs/architecture/c4-context.md` /
`c4-container.md` if asked what's inside.

## 2. Analyze a vulnerable PR (3 min)

```bash
curl -s -X POST localhost:8000/analyses -H "Content-Type: application/json" -d '{
  "repository": "secureops",
  "pull_request_number": 1,
  "commit_sha": "5555555555555555555555555555555555555555",
  "trigger": "pull_request",
  "mode": "blocking_enabled",
  "changed_files": [
    {"path": "app/routes/refunds.py", "language": "python",
     "content_ref": "/workspace/secureops/tests/fixtures/python_vulnerable/critical_unprotected_data_flow.py"}
  ]
}' | python3 -m json.tool
```

Note `mode: blocking_enabled` — call out that `advisory` is the product's
real default (`GATE_MODE` in `.env.example`); this request explicitly opts
into the restricted-blocking demo path.

Grab the `id` from the response, then:

```bash
curl -s http://localhost:8000/analyses/<id>/pr-feedback | python3 -c "import json,sys; print(json.load(sys.stdin)['comment'])"
```

Walk through one finding out loud: cause → evidence (the actual matched
source line) → impact → recommended correction → safe example. This is the
finding-completeness guarantee from Constitution Principle I — every
published finding has all five fields, deterministic fallback if Ollama
doesn't answer in time.

```bash
curl -s http://localhost:8000/analyses/<id>/gate-decision | python3 -m json.tool
```

`"decision": "blocked"` — call out *why*: not "the AI flagged it," but
`≥2 independent deterministic signals` (`app/api/gate.py`). If Ollama is
running locally, point out a possible `suggested_severity` on the finding's
`remediation` object and that it's a suggestion — accepted only through
`POST /findings/{id}/override`, never applied automatically
(Constitution Principle II).

## 3. The dashboard (1–2 min)

Refresh `http://localhost:8080` (or navigate to it fresh) — the severity
donut, weekly trend, and top-critical-files widgets now reflect the finding
from step 2. Open the findings list, filter by severity/status, click a
status badge to override it inline — this is the same
`POST /findings/{id}/override` call from Constitution Principle... US4's
governance scope: visible history, no full RBAC/audit-log system.

## 4. The gate on a real PR (2–3 min, prepare ahead of time)

This is the part that can't be faked with curl: open an actual PR against
this repo (e.g. a branch that edits a file under `secureops/tests/fixtures/`
or introduces a real, contained issue) and let
`.github/workflows/secureops-gate.yml` run. Show the Actions tab: the job
builds `secureops/Dockerfile`, starts Postgres as a service container,
POSTs the PR's real diff to `/analyses`, and either fails the check
(`blocked`) or passes it. On a same-repo PR, also point at the PR
comment/commit status SecureOps posted itself — `app/github/publisher.py`,
not a copy-pasted result.

**Do a dry run of this PR before the actual defense** — pick the fixture,
open the PR, confirm the check fails/passes as expected, and either leave
it open or close it. Don't discover a flake live.

## 5. Two languages, on purpose unequal (30s, if asked)

"Python is primary — AST rules plus taint tracking. JavaScript is
secondary, deterministic-only, one supported rule, no parity claim." Point
at `secureops/README.md`'s "Known Secondary-Language Limitations" section —
this is documented as a deliberate scope boundary
(Constitution Principle III), not something waiting to be fixed.

## Talking points if pressed on scope

- **Why isn't blocking the default?** Constitution Principle II — automatic
  blocking is opt-in and earned, never AI-authority-only. `advisory` is the
  product default; the demo above explicitly requests `blocking_enabled`.
- **What happens if Ollama is down during the defense?** Nothing breaks —
  `app/remediation/fallback.py` produces the same five required fields from
  a reviewed template. `secureops/README.md`'s Ollama-fallback section
  documents the exact expected evidence if you want to demonstrate this
  live (kill the Ollama process, re-run step 2).
- **What's not done?** `secureops/README.md`'s "Known limitations" and the
  root `README.md`'s section by the same name are current and honest —
  read from there rather than improvising.
