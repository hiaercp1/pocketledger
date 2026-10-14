# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Key Implementation Rules

- **Frontend API calls**: Always use [`apiFetch()`](../../frontend/src/api.js) — never raw `fetch()`. It handles auth token and `/api` prefix automatically. `DELETE 204` returns `null`.
- **Vite proxy strips `/api`**: Backend FastAPI routes must NOT include `/api` prefix (e.g., the health endpoint is `GET /health`, accessed from frontend as `/api/health`).
- **JSX only, no TypeScript**: Frontend uses `.jsx`/`.js`. Do not introduce `.tsx`/`.ts` files.
- **Python venv path**: `backend/.venv/` — use `.venv/bin/pytest` for tests, `.venv/bin/uvicorn` for server. Run tests from `backend/` directory.
- **New routers**: Create in `backend/routers/`, add `dependencies=[Depends(verify_token)]` on the router, register with `app.include_router(…)` in `main.py`.
- **New tests**: Add to `backend/tests/`; run single test with `.venv/bin/pytest tests/test_file.py::test_name`. Each test fixture creates its own temp DB via `monkeypatch.setenv("POCKETLEDGER_DB", …)` + `database.init_db()`.
- **Env vars**: Backend reads `POCKETLEDGER_TOKEN` (auth) and `POCKETLEDGER_DB` (SQLite path); frontend reads `VITE_API_TOKEN` (Vite exposes only `VITE_` prefixed vars).
- **Decimal, never float** for monetary amounts in Python — project standard enforced by `.bob/rules/pocketledger-standards.md`.
- **String amounts in JSON**: Pydantic models use `@field_serializer` to return `str(v)` for `Decimal` amounts. Frontend receives and sends amounts as decimal strings (e.g. `"-5.00"`).
- **No parseFloat/toFixed for display**: Use integer-cent arithmetic. See `formatDecimalAmount()` in `frontend/src/utils.js` for the pattern.
- **Expenses are negative**: Sign determines income vs expense. `isExpense` checks use `amount.startsWith('-')`.
- **No chart libraries**: Chart rendering uses Canvas 2D API only (see `CategoryChart.jsx`).
- **JSDoc on every React component**: Describe all props — required by project standards.
- **Audit log**: Append one line to `bob-audit/audit.log` after every Agent interaction: `[ISO timestamp] [mode] [brief description of change]`.
- **All endpoints require auth**: Including `GET /health`. Use `Depends(verify_token)` on every endpoint or router.
- **CSV export**: `GET /transactions/export` returns `text/csv` (bearer-protected). `/export` must be declared before `/{tx_id}` in the router to avoid FastAPI treating `export` as a path parameter. Amounts are quantized to `Decimal("0.01")`. `ExportCsvButton.jsx` uses raw `fetch()` (not `apiFetch()`) because the response is a Blob, not JSON.
