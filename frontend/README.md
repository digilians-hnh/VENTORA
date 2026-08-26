# VENTORA frontend

React + TypeScript + Vite SaaS frontend for VENTORA, talking to the read-only
`backend_api/` FastAPI service.

## Setup

```bash
cd frontend
npm install
```

## Run (development)

```bash
npm run dev
```

Opens on http://localhost:5173. Expects the API at `http://localhost:8000`
by default — see `.env.development` / `.env.example` to change this via
`VITE_API_BASE_URL`.

## Build

```bash
npm run build
```

Outputs to `dist/`. Preview the production build with `npm run preview`.

## Pages implemented (Phase 2)

- `/` — Home
- `/overview` — Executive Overview (GET /api/summary)
- `/risk-explorer` — Risk Explorer (GET /api/risk-df)
- `/recommendations` — Recommendations (GET /api/recommendations)
- `/business-impact` — Business Impact (GET /api/business-value)

Data Input / live inference / company upload are intentionally **not**
implemented yet — Phase 3.
