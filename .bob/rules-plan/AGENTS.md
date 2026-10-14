# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Design Constraints

- **No TypeScript on frontend**: The project uses plain JSX/JS — proposals must stay in `.jsx`/`.js`.
- **No linter/formatter yet**: No ESLint, Prettier, or Ruff configured — any introduced tooling is additive.
- **Vite proxy contract**: Frontend→backend communication goes through `/api/*`; backend routes live at `/*` (no `/api` prefix). Any new endpoints must follow this convention.
- **Auth token shared secret**: `POCKETLEDGER_TOKEN` (backend) and `VITE_API_TOKEN` (frontend) must be set to the same value. The root `.env.example` shows this pattern.
- **SQLite storage**: Backend is configured for a file-based SQLite DB (`POCKETLEDGER_DB`). Proposals involving the DB layer should target SQLite-compatible approaches.
- **Routers pattern**: FastAPI route modules belong in `backend/routers/` and are registered in `backend/main.py`.
