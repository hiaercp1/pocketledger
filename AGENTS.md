# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**PocketLedger** — a monorepo with a React/Vite frontend and a FastAPI/Python backend.

```
pocketledger/
├── frontend/          # React 18 + Vite (JSX, no TypeScript)
│   └── src/
│       ├── api.js     # Single API client — use apiFetch() for all backend calls
│       ├── components/
│       └── styles/
├── backend/           # FastAPI + uvicorn
│   ├── main.py        # App entry point
│   ├── routers/       # Add new route modules here
│   └── tests/
├── .env.example       # Root-level env for local dev (POCKETLEDGER_TOKEN, VITE_API_TOKEN)
├── backend/.env.example  # Backend-only env (POCKETLEDGER_TOKEN, POCKETLEDGER_DB)
└── start.sh           # One-shot dev launcher — starts both services
```

## Running / Starting

```bash
# Start both services (creates venv + installs deps automatically on first run)
./start.sh

# Backend only (from backend/)
cd backend && .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Frontend only (from frontend/)
cd frontend && npm run dev
```

## Backend Commands (run from `backend/`)

```bash
# Install deps (venv must already exist)
pip install -r requirements.txt

# Run all tests
pytest

# Run a single test file
pytest tests/test_foo.py

# Run a single test by name
pytest tests/test_foo.py::test_function_name
```

## Frontend Commands (run from `frontend/`)

```bash
npm install
npm run dev      # Vite dev server (proxies /api → http://localhost:8000)
npm run build
npm run preview
```

No linter (eslint) or formatter (prettier) is configured yet.

## Critical Patterns

- **API client**: All frontend → backend calls go through [`apiFetch()`](frontend/src/api.js) in `frontend/src/api.js`. It automatically prepends `/api`, sets `Content-Type: application/json`, and attaches the `Bearer` token from `VITE_API_TOKEN`. Never call `fetch()` directly.
- **Vite proxy**: Vite rewrites `/api/*` → `http://localhost:8000/*` (strips `/api` prefix). Backend routes must NOT include `/api` in their path.
- **Auth**: Bearer token auth on both sides — `POCKETLEDGER_TOKEN` (backend) and `VITE_API_TOKEN` (frontend). The root `.env.example` sets both; `backend/.env.example` sets backend-only variables including `POCKETLEDGER_DB` (SQLite file path).
- **Python venv**: Lives at `backend/.venv/`. Always activate or use `.venv/bin/python` / `.venv/bin/pytest`.
- **Frontend is JSX, not TSX**: No TypeScript — use `.jsx` for components, `.js` for utilities.
- **Routers**: New FastAPI route modules go in `backend/routers/`; tests go in `backend/tests/`.
- **Default dev token**: `start.sh` defaults `POCKETLEDGER_TOKEN` to `dev-token-123` if unset.
