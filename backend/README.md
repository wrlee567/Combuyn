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

Iteration 1 bootstraps the schema with `Base.metadata.create_all` on startup for
a frictionless first run. Alembic is scaffolded under `alembic/` and wired to the
ORM metadata; starting with the next schema change we generate versioned
migrations:

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

## Layout

```
app/
  config.py        settings (env-driven)
  database.py      engine, session, Base, URL normalization
  models/          ORM models (ccf.py) + cross-dialect types
  schemas/         Pydantic I/O models
  api/             routers (health.py, ccf.py)
  seed/            bundled CCF reference data + idempotent seeder
alembic/           migration environment
tests/             pytest suite (SQLite)
```
