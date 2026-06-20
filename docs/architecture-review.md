# Combuyn Architecture Review

**Date:** 2026-06-20

## Current Architecture Summary

Combuyn is a vertical-slice FastAPI + SQLAlchemy backend with a React/Vite frontend. The backend keeps a clear top-level shape: ORM models in `backend/app/models/`, Pydantic contracts in `backend/app/schemas/`, routers in `backend/app/api/`, deterministic domain functions in `backend/app/services/`, and idempotent seeders in `backend/app/seed/`. Tests run against SQLite with cross-dialect JSON handling through `JSONBType`, while production uses PostgreSQL and Alembic migrations.

The Common Control Framework and vendor modules are small enough that their routers remain understandable. The vendor router contains a little persistence orchestration, but the risk scoring engine is already pure and tested in `services/risk_scoring.py`.

AI governance is currently the largest bounded area. It spans inventory, ISO/IEC 42001 controls, EU AI Act classification, generated compliance tasks, privacy and infrastructure guardrails, impact assessments, governance reviews, evidence, vendors, Trust Center records, and medical AI risk. The current implementation preserves demo behavior and is well covered by endpoint tests, but `backend/app/api/ai_governance.py` now contains query composition and response assembly that should move to services before the router grows further.

On the frontend, `frontend/src/api.ts` owns both API contracts and the backendless demo fallback. That is intentional today: it keeps the UI easy to preview without a backend. The tradeoff is file size. `frontend/src/pages/AIGovernance.tsx` is also large, but the complexity is presentation grouping rather than business logic. `frontend/src/demoData.ts` mirrors backend seed shape and should remain behaviorally aligned with the API contracts.

Database lifecycle is already documented and appropriately cautious: local and test startup use `Base.metadata.create_all()` for frictionless setup, production disables it and relies on Alembic. This should not change without a separate ADR and validation that local/test startup remains simple.

## Refactor Candidates

| Candidate | Impact | Risk | Effort | Notes |
|---|---:|---:|---:|---|
| Move AI governance query and response assembly from `api/ai_governance.py` into service helpers | High | Low | Low | Best Phase 1 move. Keeps endpoint URLs and response schemas stable while making routers thin. |
| Add service-level tests for AI governance assembly helpers | High | Low | Low | Protects the moved logic independently from route tests. |
| Split `models/ai_governance.py` by bounded context | Medium | Medium | Medium | Good later cleanup: inventory/classification, evidence/reviews, guardrails, trust center, medical AI. Requires careful import/export compatibility. |
| Split `seed/ai_governance.py` into reference, inventory demo, review/evidence, trust center, and medical seeders | Medium | Medium | Medium | Reduces seeder size, but idempotence and ordering must be preserved. |
| Split `api/ai_governance.py` into subrouters by bounded context | Medium | Medium | Medium | Should follow service extraction. Preserve existing endpoint URLs through router prefixes. |
| Extract frontend API transport helpers from `frontend/src/api.ts` | Medium | Low | Low | Useful if the file grows further. Preserve existing exported types and `api` object. |
| Extract AI governance page sections/components from `AIGovernance.tsx` | Medium | Low | Medium | Improves readability, but should avoid UI churn. Start with pure grouping helpers/components only. |
| Split `frontend/src/demoData.ts` by domain | Low | Low | Medium | Improves navigation but creates import churn. Keep until API files split. |
| Replace startup `create_all()` with Alembic-only local flow | Low | High | Medium | Not recommended now. Current behavior intentionally supports tests and first-run local demos. |

## Recommended Phase Order

### Phase 1: Thin the AI Governance Router

Move obvious query helpers and response assembly from `backend/app/api/ai_governance.py` into `backend/app/services/ai_governance.py`. Keep route functions as dependency/adaptor code. Add service tests for latest classification, review evidence counts, and trust center assembly. Do not change schemas, URLs, database tables, seed data, or frontend behavior.

### Phase 2: Formalize AI Governance Bounded Contexts

Split AI governance backend files by context after Phase 1 proves stable:

- `inventory`: AI systems and ISO 42001 mappings.
- `classification`: EU AI Act questionnaire, risk tiers, and generated compliance tasks.
- `evidence_reviews`: governance reviews and evidence readiness.
- `guardrails`: data privacy and infrastructure validation.
- `trust_center`: public posture, transparency, and document request records.
- `medical_ai`: SOUP components and clinical/algorithmic risk.

Keep compatibility imports during the split so existing migrations, tests, and route imports remain stable.

### Phase 3: Frontend Readability Split

Extract transport helpers from `frontend/src/api.ts` only if the API client keeps growing. Then split `AIGovernance.tsx` into section components without changing the `api` object, exported types, or demo fallback. Split `demoData.ts` last, and only with tests/build confirming no backendless preview regression.

### Phase 4: Database Lifecycle Decision

Leave `Base.metadata.create_all()` in place for local/test startup. If the team wants Alembic-only startup later, write a dedicated ADR that covers local onboarding, CI fixtures, production boot order, rollback, and how new contributors initialize a database without Docker.

## Phase 1 Scope for This Change

Implement only the first candidate: move AI governance query/response assembly into services and add focused service tests. No schema changes, no broad renames, no endpoint changes, no frontend behavior changes, and no demo fallback changes.
