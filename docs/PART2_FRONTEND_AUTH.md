# Part 2 — Frontend Authentication

Handoff context for the follow-up flagged in PR #9 (Security hardening: JWT auth +
tenant isolation). That PR locked down the backend; this part makes the React
frontend work against the now-protected API.

## Why this is needed

PR #9 made every `/api/*` route (except the public `/api/trust-center`) require a
JWT bearer token whose `org_id` claim scopes data to one tenant. The frontend:

- sends **no** `Authorization` header, and
- has **no** login flow.

It also gated the demo-data fallback behind `VITE_DEMO_MODE` (PR #9). So with auth
enforced and demo mode off, every page that calls a protected endpoint will get a
`401` and surface an error state. The app is effectively unusable against a real
backend until it can obtain and send a token.

## Backend prerequisite: a token-issuance endpoint

The backend can *verify* tokens but cannot *issue* them to a browser yet.
`app/auth.py` exposes `create_access_token(org_id)` and the `current_org`
dependency, but there is **no login route**. Before/with the frontend work, add a
backend login endpoint, e.g.:

- `POST /api/auth/login` → validates credentials, returns `{ access_token, org_id }`.
- Decide the credential source. Mock-first (per CLAUDE.md, no cloud creds): a
  seeded users table or a simple env-configured demo user is fine for now.
- Reuse `create_access_token` for minting; keep HS256 + `JWT_SECRET`.
- Add a `User`/membership model carrying `org_id` if multi-user is wanted; or
  start with one demo user mapped to `DEFAULT_ORG_ID`.

Tenant scoping already works end-to-end — see `tests/test_auth.py` for the
expected 401 (unauth) and 404 (cross-tenant) behavior.

## Frontend work

### 1. Token storage + auth context
- Store the token (in-memory + `localStorage` for persistence across reloads).
- Add a small `AuthContext`/provider exposing `token`, `login()`, `logout()`,
  `isAuthenticated`.

### 2. Attach the header — single choke point
All requests go through two helpers in `frontend/src/api.ts`:
- `get<T>(path)` (line ~312)
- `send<T>(path, method, body)` (line ~318)

Add the header in both:
```ts
const headers: Record<string, string> = { "Content-Type": "application/json" };
const token = getToken();           // from auth context/storage
if (token) headers["Authorization"] = `Bearer ${token}`;
```
`BASE` is `import.meta.env.VITE_API_BASE_URL` (api.ts:22).

### 3. Handle 401 globally
- `get`/`send` already throw on `!res.ok`. On `401`, clear the token and redirect
  to the login route (the auth context can expose a handler).
- `useApi` (`frontend/src/useApi.ts`) already captures `error`; pages render it.
- Keep `getOrDemo` (api.ts:~330) as-is — demo mode is a separate, opt-in path
  (`VITE_DEMO_MODE`, typed in `frontend/src/vite-env.d.ts`).

### 4. Login UI + route guard
- Add a `Login` page and route in `frontend/src/App.tsx` (router uses
  `react-router-dom`; see existing `<Routes>`).
- Wrap the authenticated layout so unauthenticated users are redirected to
  `/login`. The public `/trust-center` page should remain reachable without auth.

### 5. Types/env
- No new `VITE_*` var strictly required (token comes from login), but if a
  bootstrap/demo token is desired, add it to `ImportMetaEnv` in
  `frontend/src/vite-env.d.ts`.

## Files to touch

| Area | File |
|---|---|
| Request helpers (add header, handle 401) | `frontend/src/api.ts` |
| Fetch hook (already surfaces errors) | `frontend/src/useApi.ts` |
| Router + guard + login route | `frontend/src/App.tsx` |
| New: auth context/provider | `frontend/src/auth/` (new) |
| New: Login page | `frontend/src/pages/Login.tsx` (new) |
| Env typing (if a token var is added) | `frontend/src/vite-env.d.ts` |
| Backend login endpoint | `backend/app/api/` (+ `app/auth.py`, schema, test) |

## Acceptance criteria

- Logging in stores a token; all pages load real data against a protected API.
- A `401` (expired/invalid token) clears auth and routes to `/login`.
- `/trust-center` works while logged out.
- Backend: login endpoint has tests; existing `tests/test_auth.py` still green.
- `cd frontend && npm run lint && npm run build` clean; `cd backend && pytest` green.

## Out of scope / open questions

- Real identity provider (OAuth/SSO) — start mock-first.
- Refresh tokens / token rotation — short-lived HS256 tokens are fine initially.
- Multi-user-per-org and roles — only if product needs it now.
- Token expiry is currently 12h (`create_access_token` in `app/auth.py`); revisit
  if a refresh strategy is added.

## Reference (already landed in PR #9)

- `backend/app/auth.py` — `create_access_token`, `current_org` (HS256, PyJWT).
- `backend/app/config.py` — `jwt_secret`, `jwt_algorithm`.
- `backend/tests/test_auth.py` — 401/404 tenant-isolation behavior + fixtures
  (`client`, `anon_client`, `other_org_client`).
- `backend/README.md` → "Authentication & tenancy".
