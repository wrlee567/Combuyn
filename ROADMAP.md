# Combuyn — Iterative Roadmap

We build **vertical slices**, not horizontal layers. Every iteration ships a working
DB → API → UI path you can click through and demo. The medical device subsystem stays
**segregated** (its own schema namespace + module) from Iteration 1 onward.

> Source of truth for *what* to build: the architectural blueprint (`Combuyn_App.docx`).
> This roadmap reorders selected blueprint phases into shippable increments.

## Status legend
- ✅ done · 🚧 in progress · ⬜ planned

---

## ✅ Iteration 0 — Foundation
Monorepo scaffold, Docker Compose (postgres + api + web), CI (backend tests + frontend build),
health check, deploy configs for **Render** (backend + Postgres) and **Vercel** (frontend).

## ✅ Iteration 1 — Common Control Framework (CCF) Core
- Tables: `frameworks`, `framework_requirements`, `common_controls`, and the
  `control_requirement_mappings` many-to-many join.
- Seeded with **real** citations: SOC 2 (CC6.1, CC6.6, CC7.2…), PCI DSS v4.0.1 (Req 3, 1, 8, 10…),
  NIST 800-53 Rev 5 (SC-28, SC-7, AC-2, AU-2…).
- API: list frameworks, list controls, control-coverage matrix.
- UI: dashboard + frameworks list + **control-coverage matrix** (one control → many frameworks).
- Multi-tenancy via `org_id` scoping (full Postgres RLS tracked for a later iteration).

## ✅ Iteration 2 — TPRM Vendors
- `vendors` table with the six-phase TPRM lifecycle (sourcing → offboarding).
- **Inherent risk scoring** engine (pure, tested): data classification × network
  connectivity × industry × geography → 0-100 score + tier + per-factor breakdown.
- JSONB-backed **dynamic security questionnaire** (template in code, answers merged
  into JSONB; partial saves don't clobber prior answers).
- API: list/create/get vendors, `/options`, `/questionnaire-template`, plus
  lifecycle + questionnaire PATCH endpoints.
- UI: Vendors list (risk-sorted), Add Vendor form, Vendor detail (profile, risk
  breakdown, lifecycle control, questionnaire); demo fallback for previews.

## ⬜ Iteration 3 — Workflow Orchestration Engine
Lightweight **durable Python state machine** (state persisted to Postgres, resumes after crash),
Saga/compensating transactions, **JSON blueprints** rendered visually with React Flow,
**observer pattern → Slack** notifications on state transitions.

## ⬜ Iteration 4 — Evidence & Continuous Compliance
`evidence` + `implemented_controls` tables. **Pluggable cloud-evidence collector** interface with a
**mock provider as default** (no AWS required). Findings map back to CCF controls and flip
compliance status in real time. Real providers (incl. Render/Vercel/GitHub APIs) drop in later.

## ⬜ Iteration 5 — BI Dashboards & ROI
Single-pane compliance posture across all frameworks, **ROI calculator** (admin hours saved),
visual **workflow execution monitor** highlighting failed nodes.

---

## Cross-cutting (threaded through every iteration)
- **Auth & multi-tenancy** — start with `org_id` scoping; harden to Postgres RLS.
- **Tests** — each slice ships API + unit tests; CI gates merges.
- **Migrations** — Alembic, additive/backward-compatible (major bump only on breaking change).
- **Deploy** — Render (api+db) + Vercel (web) kept green each iteration.
