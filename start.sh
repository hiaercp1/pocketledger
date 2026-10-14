#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Backend ──────────────────────────────────────────────────────────────────
BACKEND_DIR="$REPO_ROOT/backend"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "[start.sh] Creating Python venv at backend/.venv …"
  python3 -m venv "$BACKEND_DIR/.venv"
fi

echo "[start.sh] Installing backend dependencies …"
"$BACKEND_DIR/.venv/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# DEV-ONLY DEFAULT — "dev-token-123" is a well-known placeholder that exists
# solely to let the project start out-of-the-box on a developer's laptop.
# It MUST be overridden by setting POCKETLEDGER_TOKEN (and VITE_API_TOKEN) in
# the environment before running start.sh in any shared or production context.
export POCKETLEDGER_TOKEN="${POCKETLEDGER_TOKEN:-dev-token-123}"
export VITE_API_TOKEN="${VITE_API_TOKEN:-$POCKETLEDGER_TOKEN}"

echo "[start.sh] Starting uvicorn on :8000 …"
(cd "$BACKEND_DIR" && "$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────────────────────
FRONTEND_DIR="$REPO_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "[start.sh] Installing frontend dependencies …"
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "[start.sh] Starting Vite dev server …"
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

# ── Wait ─────────────────────────────────────────────────────────────────────
echo "[start.sh] Both services running. Press Ctrl-C to stop."
wait $BACKEND_PID $FRONTEND_PID
