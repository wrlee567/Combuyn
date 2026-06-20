# Combuyn Backend (FastAPI)

The Common Control Framework API. FastAPI + SQLAlchemy 2.0 + PostgreSQL (JSONB).

## Run locally (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # point DATABASE_URL at your Postgres
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs>.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run on in-memory SQLite — no Postgres required. The cross-dialect column
types in `app/models/types.py` let the same models target JSONB (Postgres) and
JSON (SQLite).

## Schema & migrations

Local/test runs bootstrap the schema with `Base.metadata.create_all` on startup
for a frictionless first run. This is gated by `AUTO_CREATE_SCHEMA` (defaults on
outside production, off when `ENVIRONMENT=production`).

In production, Alembic is the source of truth: the container runs
`alembic upgrade head` before the app boots (see `Dockerfile`), and `create_all`
is disabled. An initial baseline lives at
`alembic/versions/0001_initial_schema.py`. For subsequent schema changes,
generate a versioned migration (autogenerate against PostgreSQL so JSONB types
are captured correctly):

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/ready` | DB reachable + seeded |
| GET | `/api/summary` | Dashboard counts |
| GET | `/api/frameworks?category=` | List frameworks |
| GET | `/api/frameworks/{id}/requirements` | Requirements for a framework |
| GET | `/api/controls` | List common controls |
| GET | `/api/coverage` | **Control-coverage matrix** (one control → many frameworks) |
| GET | `/api/vendors` | List vendors (risk-sorted) |
| POST | `/api/vendors` | Create a vendor (computes inherent risk) |
| GET | `/api/vendors/{id}` | Vendor detail (profile, risk breakdown, answers) |
| GET | `/api/vendors/options` | Allowed risk factors + lifecycle phases |
| GET | `/api/vendors/questionnaire-template` | Security questionnaire template |
| PATCH | `/api/vendors/{id}/questionnaire` | Save questionnaire answers (merged) |
| PATCH | `/api/vendors/{id}/lifecycle` | Advance the TPRM lifecycle phase |

## Layout

```
app/
  config.py        settings (env-driven)
  database.py      engine, session, Base, URL normalization
  models/          ORM models (ccf.py, vendor.py) + cross-dialect types
  schemas/         Pydantic I/O models
  api/             routers (health.py, ccf.py, vendors.py)
  services/        domain logic (risk_scoring.py)
  seed/            bundled reference data + idempotent seeder
alembic/           migration environment
tests/             pytest suite (SQLite)
```
