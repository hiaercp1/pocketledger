# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Key Implementation Rules

- **Frontend API calls**: Always use [`apiFetch()`](../../frontend/src/api.js) — never raw `fetch()`. It handles auth token and `/api` prefix automatically.
- **Vite proxy strips `/api`**: Backend FastAPI routes must NOT include `/api` prefix (e.g., the health endpoint is `GET /health`, accessed from frontend as `/api/health`).
- **JSX only, no TypeScript**: Frontend uses `.jsx`/`.js`. Do not introduce `.tsx`/`.ts` files.
- **Python venv path**: `backend/.venv/` — use `.venv/bin/pytest` for tests, `.venv/bin/uvicorn` for server.
- **New routers**: Add FastAPI route modules to `backend/routers/`, then include them in `backend/main.py`.
- **New tests**: Add to `backend/tests/`; run single test with `pytest tests/test_file.py::test_name`.
- **Env vars**: Backend reads `POCKETLEDGER_TOKEN` and `POCKETLEDGER_DB`; frontend reads `VITE_API_TOKEN` (Vite exposes only `VITE_` prefixed vars).
