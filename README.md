# Combuyn

**Com·buy·n** — *so people will buy in to compliance.*

Combuyn is an automated, full-stack **Governance, Risk & Compliance (GRC)** platform built around
a **Common Control Framework (CCF)**: implement a control once, satisfy many frameworks at once.

It automates **Third-Party Risk Management (TPRM)** across enterprise security frameworks
(**PCI DSS v4.0.1, NIST 800-53 Rev 5, SOC 2**) and keeps a cleanly segregated **medical device
regulatory subsystem** (MDSAP, ISO 13485:2016, IEC 62304, MDR, HDS) as a scalable side feature.

> Architectural north star: the [OpenSSF Gemara](https://gemara.openssf.org/) layered GRC model and
> the [Secure Controls Framework](https://securecontrolsframework.com/) common-control approach.

---

## Why this exists

Traditional GRC lives in spreadsheets and screenshots. Combuyn pivots to an **API-driven,
continuous-compliance** posture: a single technical control maps to many regulatory requirements,
evidence is collected programmatically, and compliance status updates in real time.

## Architecture

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React + Vite + TypeScript** (Vercel) | Visual workflow builders (React Flow) + BI dashboards |
| Backend | **FastAPI** (Render) | Async-native, great for cloud collectors + the state-machine engine |
| Database | **PostgreSQL** (Render) | Relational CCF many-to-many + JSONB for dynamic questionnaires |
| Integrations | **Pluggable provider interface** | Mock by default — no cloud creds required to run |
| Notifications | **Slack** | Workflow observer/listener events |

External integrations (cloud evidence collectors, Slack) sit behind interfaces with **mock
implementations as the default**, so the entire app runs end-to-end with zero external credentials.

## Build approach — iterative vertical slices

See **[ROADMAP.md](./ROADMAP.md)**. Each iteration ships a working DB → API → UI path you can click
through. This repo currently delivers:

- **Iteration 0 — Foundation:** monorepo, Docker Compose, CI, health check, deploy configs.
- **Iteration 1 — CCF Core:** Frameworks / Requirements / Common Controls with many-to-many
  mappings, seeded with real SOC 2 / PCI DSS / NIST citations, plus a control-coverage UI.

## Quick start (local)

```bash
docker compose up --build
# API     -> http://localhost:8000  (docs at /docs)
# Web      -> http://localhost:5173
# Postgres -> localhost:5432
```

Or run pieces individually — see [`backend/README.md`](./backend/README.md) and
[`frontend/README.md`](./frontend/README.md).

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, CCF seed data, tests
frontend/   React + Vite + TS app (dashboard, frameworks, control coverage)
docker-compose.yml   Local dev: postgres + api + web
render.yaml          Render blueprint: web service + managed postgres
.github/workflows/   CI: backend tests + frontend build
```

## License

Proprietary — internal project.
