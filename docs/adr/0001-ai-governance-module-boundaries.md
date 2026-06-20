# ADR-0001: AI Governance Module Boundaries

**Status:** Accepted
**Date:** 2026-06-20
**Deciders:** Combuyn maintainers

## Context

The AI governance slice now covers inventory, ISO/IEC 42001 controls, EU AI Act classification, compliance tasks, guardrails, evidence reviews, Trust Center reporting, vendor provider posture, and medical AI risk. The API router has grown into query composition and response assembly, which conflicts with the repository convention that routers stay thin and domain/query logic lives in `services/`.

The immediate constraint is to preserve demo behavior, endpoint URLs, response fields, schemas, seed data, and local/test startup behavior.

## Decision

For Phase 1, keep the public module layout and route paths unchanged, but move AI governance query and response assembly into `backend/app/services/ai_governance.py`. Routers remain HTTP adapters: dependency injection, payload acceptance, and response return.

Future splits should follow bounded contexts:

- Inventory and ISO/IEC 42001 controls.
- EU AI Act classification and generated compliance tasks.
- Evidence and governance reviews.
- Privacy and infrastructure guardrails.
- Trust Center posture.
- Medical AI risk.

## Options Considered

### Option A: Service Extraction First

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Low |
| Scalability | Medium |
| Team familiarity | High |

**Pros:** Thin routers quickly, low behavior risk, easy to test moved logic, no route/schema churn.
**Cons:** `services/ai_governance.py` becomes larger until later bounded-context splits happen.

### Option B: Split Models, Seeders, Routers, and Services Now

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost | Medium |
| Scalability | High |
| Team familiarity | Medium |

**Pros:** Clear long-term module boundaries immediately.
**Cons:** Broad import churn, higher regression risk, harder to prove behavior preservation in one pass.

### Option C: Leave Structure As-Is

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Low |
| Scalability | Low |
| Team familiarity | High |

**Pros:** No immediate change.
**Cons:** Router keeps accumulating domain/query logic and becomes harder to split safely later.

## Trade-off Analysis

Service extraction first gives the best risk-adjusted improvement. It addresses the current architectural smell without broad renames or database changes, and it creates a stable seam for later bounded-context modules.

## Consequences

- AI governance route functions become smaller and easier to scan.
- Query and response assembly can be tested directly at the service layer.
- `services/ai_governance.py` temporarily owns both pure classification logic and database-backed read assembly.
- Later context splitting should preserve compatibility imports until callers are migrated.

## Action Items

1. [x] Move Phase 1 query/response assembly into AI governance services.
2. [x] Add service-level tests around moved helpers.
3. [ ] Split AI governance by bounded context in a later phase.
4. [ ] Keep startup schema lifecycle unchanged unless a future ADR replaces it.
