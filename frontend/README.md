# Combuyn Frontend (React + Vite + TS)

Dashboard, frameworks, and the control-coverage matrix for the CCF core.

## Run locally

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 (proxies /api to localhost:8000)
```

## Build / typecheck

```bash
npm run build    # tsc -b && vite build  -> dist/
npm run lint     # tsc --noEmit
```

## Deploy (Vercel)

- Framework preset: **Vite** (see `vercel.json`).
- Set `VITE_API_BASE_URL` to the Render backend URL (e.g. `https://combuyn-api.onrender.com`).
- SPA rewrites are configured so client-side routes work on refresh.

## Pages

- **Dashboard** — posture counts + "controls per framework" chart.
- **Frameworks** — the standards and their requirement counts.
- **Control Coverage** — the matrix proving one control → many frameworks.
