# CLAUDE.md — Combuyn orientation

**Combuyn** (*Com·buy·n* — "buy in to compliance") is an automated GRC platform built on a
**Common Control Framework (CCF)**: implement a control once, satisfy many frameworks.

> Read this file first. It exists so a fresh, scoped session can orient in one read instead
> of exploring. Keep it short and update the **Status** line as part of each task's commit.

## Architecture
- **Backend**: FastAPI + SQLAlchemy 2.0. Postgres + JSONB in prod; SQLite in tests.
- **Frontend**: React + Vite + TypeScript.
- **Deploy**: Render (API + managed Postgres), Vercel (frontend, Root Directory = `frontend`).
- **Mock-first**: runs end-to-end with zero cloud credentials.

## Layout
- `backend/app/models/` ORM (`ccf.py`, `vendor.py`, `ai_governance.py`) + `types.py`
- `backend/app/schemas/` Pydantic I/O · `backend/app/api/` routers · `backend/app/services/` pure logic
- `backend/app/seed/` reference data + idempotent seeders · `backend/tests/` pytest (SQLite)
- `frontend/src/pages/` screens · `frontend/src/api.ts` typed client + demo fallback
- `ROADMAP.md` = what to build next (vertical slices, one iteration at a time)

## Conventions (reuse these — don't reinvent)
- Cross-dialect columns via `app/models/types.py` → `JSONBType` (JSONB on PG, JSON on SQLite).
- Seeders in `app/seed/` are **idempotent** (check-before-insert); run from `main.py`
  lifespan AND `tests/conftest.py`. Adding a model/seeder means wiring **both** plus
  `app/models/__init__.py` (so `Base.metadata` sees the table).
- Domain logic = **pure, tested functions** in `services/` (e.g. `risk_scoring.py`,
  `ai_governance.py`); keep it out of routers and seed data.
- Pydantic schemas use `from_attributes=True`; use `selectinload` to avoid N+1.
- Frontend `src/api.ts` has a demo-data fallback so Vercel previews render without a backend.
  When adding an API, add its types + method here AND keep existing ones intact.

## Run & test
- Full stack: `docker compose up --build` (web :5173, api :8000/docs, postgres :5432)
- Backend tests: `cd backend && pip install -r requirements-dev.txt && pytest` (SQLite, no PG)
- Frontend: `cd frontend && npm install && npm run lint && npm run build`

## Branch / PR rules
- Feature branch → PR into `main`. Both CI jobs (backend, frontend) must be green.
- Don't push to a branch you weren't asked to. Don't open a PR unless asked.

## Working style (token-frugal)
- **One task per session.** Start fresh between unrelated tasks.
- Prefer scoped `Grep`/`Glob` and partial reads over whole files.
- For CI triage use `pull_request_read` (get_check_runs/get_status) + `get_job_logs` with a
  small `tail_lines`; avoid broad GitHub list calls (huge repeated metadata).

## Status
- ✅ Iter 0 Foundation · ✅ Iter 1 CCF Core · ✅ Iter 2 TPRM Vendors (PR #2 → `main`, CI green).
- 🚧 AI Governance module on branch `codex/ai-governance` (ISO 42001, EU AI Act, NIST AI RMF,
  Trust Center). **Good module, but it regressed Iter 2 wiring** — CI red. Additive fix:
  re-plug vendors in `backend/app/main.py`, `backend/app/models/__init__.py`,
  `backend/tests/conftest.py`, and the vendor surface in `frontend/src/api.ts`.
- ⬜ Next per ROADMAP: Iter 3 Workflow Orchestration Engine.
