# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Architecture Summary

- **Backend**: FastAPI (`backend/main.py`) on `:8000`, bearer-token auth via `POCKETLEDGER_TOKEN` (read at request time, not startup), SQLite via `POCKETLEDGER_DB` (defaults to `backend/pocketledger.db` resolved relative to `database.py`), venv at `backend/.venv/`.
- **Frontend**: React 18 + Vite (JSX only) on `:5173`, all API calls through [`apiFetch()`](../../frontend/src/api.js) which prepends `/api` and sets `Authorization: Bearer`.
- **Proxy**: Vite dev server rewrites `/api/*` → `http://localhost:8000/*` (strips prefix). Production deployment must replicate this rewrite.
- **Auth flow**: Both sides must share the same token value (`POCKETLEDGER_TOKEN` == `VITE_API_TOKEN`). Every endpoint including `/health` is protected. Token is compared with `secrets.compare_digest`.
- **Start**: `./start.sh` bootstraps venv, installs deps, and starts both services. Default dev token is `dev-token-123` (publicly known, dev-only).
- **Data model**: Amounts stored as integer cents in SQLite; Python uses `Decimal`; JSON uses decimal strings (e.g. `"12.50"`, `"-5.00"`). Expenses are negative amounts.
- **Category filter (F7)**: Client-side only — no server-side filtering endpoint.
- **Chart (F6)**: Canvas 2D API, no chart library. `ResizeObserver` watches container width; `totalsRef` pattern prevents stale-closure bugs.
