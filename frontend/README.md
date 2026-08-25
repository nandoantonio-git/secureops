# SecureOps Dashboard

React and TypeScript dashboard for the SecureOps analytics API. It shows severity distribution, weekly trends, critical files, and a paginated findings list with reviewer status overrides.

## Local setup

```bash
npm ci
npm run dev
```

The tracked `.env.development` provides local defaults. Use the ignored `.env.development.local` for machine-specific overrides:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_DASHBOARD_REPOSITORY=secureops/example-service
VITE_DASHBOARD_GATE_MODE=advisory
```

`VITE_DASHBOARD_REPOSITORY` is required. `VITE_DASHBOARD_GATE_MODE` must mirror the backend setting because the API does not currently expose gate mode.

## Quality checks

```bash
npm run lint       # Oxlint checks
npm test           # Vitest component tests
npm run build      # TypeScript check and production bundle
npm run preview    # Serve the production bundle locally
```

Keep API contracts in `src/api/`, reusable UI in `src/components/shared/`, dashboard widgets in `src/components/dashboard/`, and design constants in `src/design/tokens.ts`.
