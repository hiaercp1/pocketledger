# PocketLedger — Implementation Plan

## Overview

PocketLedger is a personal finance tracker with a FastAPI backend (Python 3.11+, SQLite) and a React 18 + Vite frontend. All monetary amounts are stored as integer cents in SQLite and surfaced as Decimal in Python. A static bearer token (env var `POCKETLEDGER_TOKEN`) protects every API endpoint. A root `start.sh` launches both services.

---

## Project Structure

```
pocketledger/
├── docs/
│   └── PLAN.md                  # this file
├── backend/
│   ├── main.py                  # uvicorn entrypoint, FastAPI app, router registration
│   ├── database.py              # SQLite connection helper, schema init (CREATE TABLE IF NOT EXISTS)
│   ├── models.py                # Pydantic request/response models (amounts as Decimal)
│   ├── auth.py                  # Bearer-token dependency (reads POCKETLEDGER_TOKEN)
│   ├── routers/
│   │   ├── transactions.py      # POST /api/transactions, GET /api/transactions, DELETE /api/transactions/{id}
│   │   └── summary.py           # GET /api/summary/balance, GET /api/summary/categories
│   ├── requirements.txt         # fastapi, uvicorn[standard], pydantic
│   └── tests/
│       └── test_data_layer.py   # 5+ pytest unit tests for DB/data layer
├── frontend/
│   ├── index.html
│   ├── vite.config.js           # proxy /api -> http://localhost:8000
│   ├── package.json
│   └── src/
│       ├── main.jsx             # React DOM root
│       ├── App.jsx              # top-level layout, state, routing between views
│       ├── api.js               # fetch wrapper (injects Authorization header)
│       ├── components/
│       │   ├── AddTransaction.jsx    # F1 form
│       │   ├── TransactionList.jsx   # F2 list + F7 category filter dropdown
│       │   ├── BalanceDisplay.jsx    # F4 live balance
│       │   ├── CategoryBreakdown.jsx # F5 aggregated totals table
│       │   └── CategoryChart.jsx     # F6 canvas bar chart
│       └── styles/
│           └── main.css             # plain CSS, no framework
├── start.sh                     # starts backend (port 8000) + Vite dev server
└── .env.example                 # POCKETLEDGER_TOKEN=changeme
```

---

## Sub-Tasks

---

### ST-1 — Project Scaffolding

**Status:** `[ ] pending`

**Intent**
Establish the skeleton directories, dependency files, and environment config so every subsequent sub-task can be developed and run in isolation.

**Expected Outcomes**
- `backend/requirements.txt` lists `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `httpx` (for test client).
- `frontend/package.json` declares `react`, `react-dom`, `vite`, `@vitejs/plugin-react`.
- `frontend/vite.config.js` proxies `/api` to `http://localhost:8000`.
- `.env.example` contains `POCKETLEDGER_TOKEN=changeme`.
- `start.sh` is executable and launches both services with `&` / `wait`.
- All directories in the structure above exist.

**Todo List**
- [ ] Create `backend/` directory structure (`routers/`, `tests/`).
- [ ] Write `backend/requirements.txt` with `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `httpx`.
- [ ] Create `frontend/` with `index.html`, `package.json`, `vite.config.js`, `src/main.jsx`, `src/App.jsx`, `src/api.js`.
- [ ] Create `frontend/src/components/` and `frontend/src/styles/main.css` (empty placeholder).
- [ ] Write `.env.example` with `POCKETLEDGER_TOKEN=changeme`.
- [ ] Write `start.sh` that activates venv, sets env, starts `uvicorn main:app` from `backend/`, then `npm run dev` from `frontend/`.

**Relevant Context**
- Vite proxy config: `server.proxy['/api'] = 'http://localhost:8000'`
- `start.sh` must `cd` into each directory or set `PYTHONPATH`/`APP_DIR` so uvicorn finds `main:app`.

---

### ST-2 — Backend: Database Layer

**Status:** `[ ] pending`

**Intent**
Implement the SQLite schema and all raw DB operations (insert, select, delete, aggregate). This is the only place SQL runs. All other layers call these functions.

**Expected Outcomes**
- `database.py` exports: `init_db()`, `add_transaction()`, `list_transactions()`, `delete_transaction()`, `get_balance()`, `get_category_totals()`.
- Schema: table `transactions` with columns `id INTEGER PRIMARY KEY AUTOINCREMENT`, `amount_cents INTEGER NOT NULL`, `description TEXT NOT NULL`, `category TEXT NOT NULL`, `date TEXT NOT NULL` (ISO-8601 string).
- `init_db()` is called once at app startup via a FastAPI `lifespan` handler.
- Amounts are stored as integer cents; `add_transaction` accepts a `Decimal`, converts to cents; `list_transactions` returns cents (callers convert back).
- DB file path read from env var `POCKETLEDGER_DB` defaulting to `ledger.db`.

**Todo List**
- [ ] Write `backend/database.py` with `get_connection()` helper returning a `sqlite3.Connection` (row_factory = `sqlite3.Row`).
- [ ] Implement `init_db()`: creates `transactions` table if not exists.
- [ ] Implement `add_transaction(amount: Decimal, description: str, category: str, date: str) -> int` (returns new row id).
- [ ] Implement `list_transactions() -> list[sqlite3.Row]` ordered by `date DESC`, then `id DESC`.
- [ ] Implement `delete_transaction(tx_id: int) -> bool` (returns False if row not found).
- [ ] Implement `get_balance() -> int` (SUM of `amount_cents`, returns 0 if empty).
- [ ] Implement `get_category_totals() -> list[dict]` (category, total_cents) ordered by total descending.

**Relevant Context**
- Use `sqlite3.connect()` with the path from env; do NOT use a global connection — open/close per call to stay thread-safe with uvicorn workers.
- `Decimal` → cents: `int(amount * 100)`. Cents → `Decimal`: `Decimal(cents) / 100`.

---

### ST-3 — Backend: Auth & Pydantic Models

**Status:** `[ ] pending`

**Intent**
Define the bearer-token auth dependency and the Pydantic request/response schemas. These are shared by all routers.

**Expected Outcomes**
- `auth.py` exports a FastAPI `Depends`-compatible function that reads `Authorization: Bearer <token>` and raises `HTTP 401` if the token doesn't match `POCKETLEDGER_TOKEN`.
- `models.py` exports:
  - `TransactionCreate` — `amount: Decimal`, `description: str`, `category: str`, `date: str` (YYYY-MM-DD).
  - `TransactionResponse` — same fields plus `id: int`; `amount` as `Decimal`.
  - `BalanceResponse` — `balance: Decimal`.
  - `CategoryTotal` — `category: str`, `total: Decimal`.

**Todo List**
- [ ] Write `backend/auth.py`: read `POCKETLEDGER_TOKEN` from `os.environ`; dependency raises `HTTPException(401)` on missing or wrong token.
- [ ] Write `backend/models.py` with the four models above.
- [ ] Ensure `Decimal` fields use `Annotated` / `condecimal` or `Decimal` directly; configure Pydantic to serialize `Decimal` as a string in JSON responses to avoid float precision loss.

**Relevant Context**
- FastAPI security: use `fastapi.security.HTTPBearer` or manually parse the `Authorization` header.
- Pydantic v2: use `model_config = ConfigDict(json_encoders={Decimal: str})` or `field_serializer`.

---

### ST-4 — Backend: API Routers

**Status:** `[ ] pending`

**Intent**
Wire the HTTP endpoints in two routers and register them on the app. All endpoints require the auth dependency.

**Expected Outcomes**
- `POST /api/transactions` — validates `TransactionCreate`, calls `add_transaction`, returns `TransactionResponse` with HTTP 201.
- `GET /api/transactions` — calls `list_transactions`, returns `list[TransactionResponse]`.
- `DELETE /api/transactions/{id}` — calls `delete_transaction`, returns HTTP 204 on success, 404 if not found.
- `GET /api/summary/balance` — calls `get_balance`, returns `BalanceResponse`.
- `GET /api/summary/categories` — calls `get_category_totals`, returns `list[CategoryTotal]`.
- `backend/main.py` instantiates the FastAPI app, includes both routers under prefix `/api`, and calls `init_db()` in a lifespan handler.

**Todo List**
- [ ] Write `backend/routers/transactions.py` with `POST`, `GET`, `DELETE` endpoints; inject auth dependency on each route (or at router level).
- [ ] Write `backend/routers/summary.py` with balance and category endpoints; inject auth dependency.
- [ ] Write `backend/main.py`: create app with `lifespan`, include routers, set CORS to allow `http://localhost:5173`.
- [ ] Verify cents↔Decimal conversion in routers: receive Decimal from model → pass to DB as cents → return Decimal to client.

**Relevant Context**
- Router-level auth: `APIRouter(dependencies=[Depends(verify_token)])`.
- CORS: `fastapi.middleware.cors.CORSMiddleware`, allow `http://localhost:5173`, methods `["*"]`, headers `["*"]`.

---

### ST-5 — Backend: Tests

**Status:** `[ ] pending`

**Intent**
Write at least 5 pytest unit tests that exercise the data layer (`database.py`) directly, using an in-memory or temp-file SQLite DB so no production DB is touched.

**Expected Outcomes**
- `backend/tests/test_data_layer.py` contains ≥ 5 tests.
- Tests use a `pytest` fixture that creates an isolated DB (`:memory:` or `tmp_path`), calls `init_db()`, and tears down after each test.
- Tests cover: insert and retrieve a transaction, list order (newest first), delete existing row returns True, delete non-existent row returns False, balance equals sum of inserted amounts, category totals aggregate correctly.

**Todo List**
- [ ] Write `conftest.py` (or inline fixture in test file) that patches the DB path to a temp file or overrides `get_connection` to use `:memory:`.
- [ ] Test: `add_transaction` inserts a row retrievable by `list_transactions`.
- [ ] Test: `list_transactions` returns newest date first.
- [ ] Test: `delete_transaction` returns `True` for existing id, `False` for unknown id.
- [ ] Test: `get_balance` returns correct sum (including signed negatives for expenses).
- [ ] Test: `get_category_totals` groups and sums correctly across multiple categories.

**Relevant Context**
- Because `get_connection` opens a new connection each call, the simplest isolation is to set `POCKETLEDGER_DB` env var to a `tmp_path` file per test, or monkeypatch `database.DB_PATH`.

---

### ST-6 — Frontend: API Client & App Shell

**Status:** `[ ] pending`

**Intent**
Build the React entry point, the fetch wrapper that attaches the auth token, and the top-level `App` component that holds global state (transactions, balance, category totals) and renders all sub-components.

**Expected Outcomes**
- `src/api.js` exports `apiFetch(path, options)` that prepends `/api`, adds `Authorization: Bearer <token>` from `import.meta.env.VITE_API_TOKEN`, returns parsed JSON.
- `src/App.jsx` fetches transactions, balance, and category totals on mount and after each mutation; passes data and callbacks as props.
- `src/main.jsx` mounts `<App />` into `#root`.
- `index.html` has `<div id="root">`.

**Todo List**
- [ ] Write `src/api.js` with `apiFetch`.
- [ ] Write `src/App.jsx`: state for `transactions`, `balance`, `categoryTotals`, `filterCategory`; `useEffect` to load all three on mount; `addTransaction`, `deleteTransaction` callbacks that call the API then refresh state.
- [ ] Write `src/main.jsx`.
- [ ] Write `index.html` with `<script type="module" src="/src/main.jsx">`.
- [ ] Add `VITE_API_TOKEN=changeme` to `.env.example` and document it.

**Relevant Context**
- Vite exposes `VITE_*` env vars to the browser via `import.meta.env`.
- Token must match `POCKETLEDGER_TOKEN` on the backend.

---

### ST-7 — Frontend: Transaction Components (F1, F2, F3, F7)

**Status:** `[ ] pending`

**Intent**
Build the form to add a transaction and the filterable, deletable list of transactions.

**Expected Outcomes**
- `AddTransaction.jsx` renders a form with fields for amount (text input, validated as numeric), description, category (text), date (date picker); submits via `onAdd` prop callback; clears on success.
- `TransactionList.jsx` accepts `transactions`, `onDelete`, `filterCategory`, `onFilterChange` props; renders a `<select>` dropdown populated from unique categories plus "All"; renders each transaction row with a Delete button; orders newest first (already sorted by API).
- Amounts displayed to 2 decimal places with sign (negative = expense, positive = income).

**Todo List**
- [ ] Write `AddTransaction.jsx` with controlled inputs and form submission.
- [ ] Write `TransactionList.jsx` with category dropdown and mapped rows.
- [ ] Apply filter: when `filterCategory` is set, `filter()` the transactions array client-side before rendering.
- [ ] Style form and list in `main.css` — clean, readable layout.

**Relevant Context**
- Amount validation: `Decimal` is enforced on the backend; the frontend should reject non-numeric input before sending.
- The dropdown's option list should be derived from the full (unfiltered) transactions list so all categories are always visible.

---

### ST-8 — Frontend: Balance, Category Breakdown & Canvas Chart (F4, F5, F6)

**Status:** `[ ] pending`

**Intent**
Display the live balance, a category totals table, and a custom horizontal bar chart drawn with the Canvas API — no external charting library.

**Expected Outcomes**
- `BalanceDisplay.jsx` renders the current balance formatted to 2 decimal places; color-coded green if ≥ 0, red if negative.
- `CategoryBreakdown.jsx` renders a `<table>` of category → total (formatted Decimal), sorted by total descending (already sorted by API).
- `CategoryChart.jsx` draws a horizontal bar chart onto a `<canvas>` element using `useRef` + `useEffect`; bars are proportional to the absolute category total; each bar is labeled with category name and value; uses `ctx.fillRect` — no library.

**Todo List**
- [ ] Write `BalanceDisplay.jsx`.
- [ ] Write `CategoryBreakdown.jsx`.
- [ ] Write `CategoryChart.jsx`: compute max value, iterate categories, draw background rect then filled bar, draw text labels.
- [ ] Ensure the canvas redraws whenever `categoryTotals` prop changes (dependency array in `useEffect`).
- [ ] Set a fixed canvas width and compute bar height from number of categories; canvas height = `numCategories * rowHeight + padding`.

**Relevant Context**
- Canvas 2D API: `canvas.getContext('2d')`, `ctx.fillStyle`, `ctx.fillRect(x, y, width, height)`, `ctx.fillText`.
- Amounts from the API are strings (Decimal serialized); parse with `parseFloat` for chart math only.

---

### ST-9 — Integration & Smoke Test

**Status:** `[ ] pending`

**Intent**
Verify the full stack works end-to-end: `start.sh` launches both services, the frontend can perform all CRUD operations, the balance updates live, the chart renders, and the auth guard blocks unauthenticated requests.

**Expected Outcomes**
- `start.sh` exits cleanly and both servers start.
- Adding a transaction via the UI appears in the list and updates balance and chart.
- Deleting a transaction reflects immediately.
- Filtering by category hides unmatched rows.
- A raw `curl` without a token returns 401; with the correct token returns 200.
- `pytest backend/tests/` passes all ≥ 5 tests.

**Todo List**
- [ ] Run `pip install -r backend/requirements.txt` and `npm install` in `frontend/`.
- [ ] Run `pytest backend/tests/` — all tests must pass.
- [ ] Start backend manually, run `curl` auth check.
- [ ] Run `start.sh` and exercise all features in the browser.
- [ ] Fix any issues found during smoke test.

---

## Data Flow Diagram

```
Browser (React)
    |
    | fetch /api/* + Authorization header
    v
Vite Dev Server (proxy /api -> :8000)
    |
    v
FastAPI (main.py)
    |-- verify_token dependency (auth.py)
    |-- /api/transactions  (routers/transactions.py)
    |-- /api/summary/*     (routers/summary.py)
    |
    v
database.py (sqlite3)
    |
    v
ledger.db (SQLite file)
```

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Amount storage | Integer cents in SQLite | Avoids float rounding; easy arithmetic in SQL |
| Amount in API | Decimal serialized as string | Preserves precision across JSON boundary |
| Auth mechanism | Static bearer token from env | Simplest auth satisfying F9; no sessions needed |
| DB per request | New connection per call | Thread-safe with uvicorn default workers |
| Filter location | Client-side in TransactionList | Avoids extra API call; data already loaded |
| Chart library | Vanilla Canvas API | Constraint F6; horizontal bars via fillRect |
