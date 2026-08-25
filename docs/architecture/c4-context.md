# C4 — System Context

Who and what SecureOps talks to, at the boundary of the system. See
[c4-container.md](c4-container.md) for what's inside the SecureOps box.

```mermaid
C4Context
    title SecureOps — System Context

    Person(reviewer, "Developer / Reviewer", "Opens or reviews a Pull Request")

    System(secureops, "SecureOps", "PR-first vulnerability feedback service: scans changed files, publishes structured findings, computes a gate decision")

    System_Ext(github, "GitHub", "Hosts the repository; triggers CI on pull_request; receives PR comments and commit status")
    SystemDb_Ext(postgres, "PostgreSQL", "Best-effort persistence of analyses, findings, remediations, overrides")
    System_Ext(ollama, "Ollama (local)", "Local LLM: contextualizes remediation text and suggests a severity re-classification")

    Rel(reviewer, github, "Opens PR, reads comment/status, reviews findings on the dashboard")
    Rel(github, secureops, "pull_request event dispatches the gate workflow, which calls POST /analyses", "HTTPS")
    Rel(secureops, github, "Posts feedback comment + commit status (best-effort, same-repo PRs only)", "GitHub API")
    Rel(secureops, postgres, "Persists / reads analyses, findings, overrides (failures swallowed, never block the response)", "SQL")
    Rel(secureops, ollama, "Requests contextualized remediation + severity suggestion (falls back to reviewed templates when unavailable)", "HTTP")
```

**Reading this diagram**: every external relationship on the SecureOps side
is designed to degrade, not fail, when the other system is slow or down —
Postgres failures are swallowed (`app/api/analyses.py`), Ollama failures
fall back to reviewed templates (`app/remediation/service.py`), and GitHub
publish failures return a `PublishResult(published=False, ...)` instead of
raising (`app/github/publisher.py`). Only GitHub-as-trigger is a hard
dependency: without a `pull_request` event (or an equivalent manual
`POST /analyses`), there is nothing to analyze.
