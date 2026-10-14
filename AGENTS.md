# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**PocketLedger** — a monorepo with a React/Vite frontend and a FastAPI/Python backend.

```
pocketledger/
├── frontend/          # React 18 + Vite (JSX, no TypeScript)
│   └── src/
│       ├── api.js     # Single API client — use apiFetch() for all backend calls
│       ├── utils.js   # formatDecimalAmount() — integer-cent currency formatting
│       ├── components/
│       └── styles/
├── backend/           # FastAPI + uvicorn
│   ├── main.py        # App entry point + CORS + lifespan DB init
│   ├── auth.py        # Bearer-token dependency (verify_token)
│   ├── database.py    # SQLite data layer — all SQL lives here
│   ├── models.py      # Pydantic models with Decimal→string serialization
│   ├── routers/       # Add new route modules here, register in main.py
│   └── tests/
├── .bob/rules/pocketledger-standards.md  # Enforced team standards (see below)
├── bob-audit/audit.log                   # Append one line after every Agent interaction
├── ledger-review/                        # Output directory for ledger-reviewer mode
└── start.sh           # One-shot dev launcher — starts both services
```

## Two-Service Architecture

- **Backend**: FastAPI on `:8000`, started from `backend/` with uvicorn.
- **Frontend**: React/Vite on `:5173`. Vite dev server proxies `/api/*` → `http://localhost:8000/*`, **stripping the `/api` prefix**. Backend routes must therefore live at `/*` (e.g. `GET /health`, not `GET /api/health`).
- **`start.sh`**: Bootstraps venv (if missing), installs deps, exports token env vars, then starts both services. Sets `POCKETLEDGER_TOKEN` and `VITE_API_TOKEN` to `dev-token-123` if unset — **this default is dev-only and publicly known**.

## Commands

```bash
# Start both services (creates venv + installs npm deps on first run)
./start.sh

# Backend only (from backend/)
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Run all backend tests (from backend/)
.venv/bin/pytest

# Run a single test by name
.venv/bin/pytest tests/test_api.py::test_function_name

# Frontend (from frontend/)
npm run dev      # Vite dev server on :5173
npm run build
```

No ESLint, Prettier, or Ruff configured.

## Authentication

- **Static bearer token** shared between both services: `POCKETLEDGER_TOKEN` (backend) and `VITE_API_TOKEN` (frontend).
- `auth.py` reads `POCKETLEDGER_TOKEN` **at request time** (not at startup) so tests can monkeypatch it freely.
- Every endpoint — including `GET /health` — requires `Depends(verify_token)`. The check uses `secrets.compare_digest` to prevent timing attacks and rejects empty tokens on either side.
- `apiFetch()` in `frontend/src/api.js` automatically attaches `Authorization: Bearer <VITE_API_TOKEN>` and prepends `/api` to all paths. Never call `fetch()` directly.

## Database Layer

- **SQLite** via stdlib `sqlite3`. DB file defaults to `backend/pocketledger.db` (resolved relative to `database.py`, not cwd). Override with `POCKETLEDGER_DB`.
- **Integer cents storage**: amounts are stored as `amount_cents INTEGER`. No floats in storage or SQL.
- **Decimal in Python**: All amount handling uses `Decimal`, never `float` (enforced project standard).
- **String amounts in JSON**: Pydantic models serialize `Decimal` as `str` via `@field_serializer` to avoid float precision loss across the JSON boundary. Frontend receives and sends amounts as decimal strings (e.g. `"12.50"`, `"-5.00"`).
- **Connection per call**: `get_connection()` opens a new `sqlite3.Connection` on every call (no connection pool). Callers use it as a context manager.
- **Parameterized queries only** — no string interpolation in SQL.

## Key Architectural Decisions

- **Expenses are negative amounts**: The sign is the sole indicator of income vs expense. The form applies a `-` prefix for expenses before sending to the API. `isExpense` checks are done via `total.startsWith('-')` on the frontend.
- **No chart libraries**: `CategoryChart.jsx` uses the Canvas 2D API directly (no Recharts, Chart.js, etc.). It handles HiDPI via `devicePixelRatio` scaling and adapts to container width via `ResizeObserver`.
- **ResizeObserver / stale-closure gotcha**: `CategoryChart`'s `draw` callback is wrapped in `useCallback(…, [])` (stable ref). A `totalsRef` is updated on every render so the `ResizeObserver` closure always reads current data. The draw `useEffect` intentionally lists `categoryTotals` (not `draw`) to avoid infinite loops.
- **Category filter is client-side (F7)**: `TransactionList` filters from the full unfiltered array in state — no extra API call.
- **Plain CSS**: `frontend/src/styles/main.css` — no CSS framework, no CSS modules.
- **Integer-cent arithmetic in the frontend**: `formatDecimalAmount()` in `utils.js` and inline `formatAmount()` in `TransactionList.jsx` both parse the decimal string using integer arithmetic to avoid IEEE 754 drift. Never use `parseFloat` / `toFixed` for display amounts.

## Bob Workflow Rules

- **Mandatory audit log**: After every Agent mode interaction, append one line to `bob-audit/audit.log` in the format:
  ```
  [ISO timestamp] [mode] [brief description of change]
  ```
- **JSDoc on every React component**: All components must have a JSDoc comment describing their props (see `pocketledger-standards.md`).
- **Decimal, never float** in Python for monetary values (enforced by `pocketledger-standards.md`).
- **`ledger-reviewer` mode**: A read-only review mode (no write tools). Place review output in `ledger-review/`. Use for pre-merge security and correctness audits.
- **One feature per task**: Work in focused, single-feature increments.

## Testing

- Tests live in `backend/tests/` (`test_api.py` — integration via `TestClient`, `test_data_layer.py` — unit).
- `conftest.py` adds `backend/` to `sys.path`; `pytest.ini` sets `testpaths = tests`.
- Each test fixture creates an isolated temp SQLite DB via `monkeypatch.setenv("POCKETLEDGER_DB", …)` and `database.init_db()`.
- Run from `backend/` directory using `.venv/bin/pytest`.

## Critical Patterns

- **API client**: Use `apiFetch(path, options)` — it prepends `/api`, sets `Content-Type: application/json`, and attaches the Bearer token. `DELETE 204` returns `null`.
- **New routers**: Create in `backend/routers/`, add `dependencies=[Depends(verify_token)]` on the router, then `app.include_router(…)` in `main.py`.
- **New Pydantic models with amounts**: Use `Decimal` fields + `@field_serializer` that returns `str(v)`.
- **Python venv**: `backend/.venv/` — use `.venv/bin/pytest`, `.venv/bin/uvicorn`, etc.
- **JSX only**: `.jsx` for components, `.js` for utilities. No TypeScript.

## CSV Export (issue #1)

- **Endpoint**: `GET /transactions/export` — bearer-protected, returns `text/csv` with `Content-Disposition: attachment; filename=transactions.csv`.
- **Columns**: `id, date, description, category, amount` — newest first, same order as `GET /transactions`.
- **Amount format**: `Decimal` quantized to exactly 2 decimal places (e.g. `"-5.00"`) via `.quantize(Decimal("0.01"))`.
- **Route-ordering gotcha**: `/export` must be declared **before** `/{tx_id}` in the router; otherwise FastAPI matches `export` as a path parameter. See [`transactions.py`](backend/routers/transactions.py:58).
- **Frontend**: `ExportCsvButton.jsx` cannot use `apiFetch()` because the response is a `Blob`, not JSON. It calls `fetch('/api/transactions/export', …)` directly with the bearer token, creates a temporary `<a>` element, triggers `.click()`, then revokes the object URL.

## Known Limitations

- No pagination on `GET /transactions` — returns all rows.
- No user accounts — single shared ledger protected only by the static token.
- Category filter (F7) is frontend-only; no server-side filtering.
- No production build/deploy config — `start.sh` is development only.
- No HTTPS in `start.sh`; CORS origin is hardcoded to `http://localhost:5173`.
