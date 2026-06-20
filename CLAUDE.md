# CLAUDE.md — Combuyn

GRC platform on a **Common Control Framework** (implement a control once, satisfy many
frameworks). Read this first; update **Status** as part of each task's commit.

## Stack
FastAPI + SQLAlchemy 2.0 (Postgres/JSONB; SQLite in tests) · React + Vite + TS ·
Render (API+DB) + Vercel (frontend, root `frontend`) · mock-first, no cloud creds.

## Layout
`backend/app/`: `models/` (+ `types.py`), `schemas/`, `api/`, `services/`, `seed/`;
`tests/` (pytest, SQLite). `frontend/src/`: `pages/`, `api.ts`. `ROADMAP.md` = next work.

## Conventions
- Cross-dialect columns via `models/types.py` → `JSONBType`.
- Seeders in `seed/` are idempotent; wire new models in `main.py` lifespan,
  `tests/conftest.py`, AND `models/__init__.py`.
- Domain logic = pure tested functions in `services/`, not routers/seed.
- Schemas use `from_attributes`; use `selectinload` to avoid N+1.
- `frontend/src/api.ts` has a demo fallback so previews render backendless; keep existing
  types/methods intact when adding new ones.

## Run / test
`docker compose up --build` (web :5173, api :8000/docs) ·
`cd backend && pytest` · `cd frontend && npm run lint && npm run build`

## Rules
Feature branch → PR into `main`; both CI jobs green. One task per session.

## Status
✅ Iter 0–3 (Foundation, CCF, TPRM Vendors, Workflow Orchestration). Iter 3 adds a durable
state machine (`workflow_definitions`/`workflow_instances`/`workflow_events`), a pure engine in
`services/workflow_engine.py`, Saga compensation + observer→mock-Slack notifications, and the
Workflows UI — wired in `main.py`, `models/__init__.py`, `conftest.py`, `api.ts`.
⬜ Next: Iter 4 (Evidence & Compliance) → Iter 5 (BI Dashboards & ROI).
