# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Design Constraints

- **No TypeScript on frontend**: The project uses plain JSX/JS — proposals must stay in `.jsx`/`.js`.
- **No linter/formatter**: No ESLint, Prettier, or Ruff configured — any introduced tooling is additive.
- **Vite proxy contract**: Frontend→backend communication goes through `/api/*`; backend routes live at `/*` (no `/api` prefix). Any new endpoints must follow this convention.
- **Auth token shared secret**: `POCKETLEDGER_TOKEN` (backend) and `VITE_API_TOKEN` (frontend) must be set to the same value. Every endpoint must be protected — including health checks.
- **SQLite storage, integer cents**: Amounts stored as `amount_cents INTEGER`. No floats in DB or Python business logic — use `Decimal`. JSON uses decimal strings.
- **Expenses are negative**: There is no separate `type` field in the DB — sign encodes income vs expense.
- **No chart libraries**: The chart component uses Canvas 2D API only. Any new visualisation proposal must also use Canvas.
- **No CSS framework**: Plain CSS only (`frontend/src/styles/main.css`). No CSS modules, Tailwind, etc.
- **Routers pattern**: FastAPI route modules belong in `backend/routers/`, must include `dependencies=[Depends(verify_token)]`, and are registered in `backend/main.py`.
- **String amounts across JSON boundary**: Pydantic `@field_serializer` returns `str(v)` for `Decimal` amounts — preserve this contract in any new model.
- **Category filter is client-side**: No server-side filter endpoint exists (F7). Any proposal for server-side filtering requires a new endpoint.
- **Single shared ledger**: No user accounts. New features must assume a single-tenant model unless an explicit multi-tenant redesign is in scope.
- **Bob workflow**: Proposals must include audit log entries, JSDoc on new React components, and should be reviewed via ledger-reviewer mode before merge.
