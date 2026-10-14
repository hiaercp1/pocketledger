# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Architecture Summary

- **Backend**: FastAPI (`backend/main.py`), bearer-token auth via `POCKETLEDGER_TOKEN`, SQLite via `POCKETLEDGER_DB`, venv at `backend/.venv/`.
- **Frontend**: React 18 + Vite (JSX only), all API calls through [`apiFetch()`](../../frontend/src/api.js) which prepends `/api` and sets `Authorization: Bearer`.
- **Proxy**: Vite dev server rewrites `/api/*` → `http://localhost:8000/*` (strips prefix). Production deployment must replicate this rewrite.
- **Auth flow**: Both sides must share the same token value (`POCKETLEDGER_TOKEN` == `VITE_API_TOKEN`).
- **Start**: `./start.sh` from repo root bootstraps venv, installs deps, and starts both services. Default dev token is `dev-token-123`.
