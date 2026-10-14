"""SQLite data layer for PocketLedger.

All SQL lives here. Amounts are stored as integer cents; callers that need
Decimal values are responsible for the conversion.
"""

import os
import sqlite3
from decimal import Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent / "pocketledger.db")
DB_PATH: str = os.environ.get("POCKETLEDGER_DB", _DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection for the current call.

    A new connection is created on every call so the module is safe with
    multiple uvicorn threads/workers. The caller must close it (use as a
    context manager).
    """
    path = os.environ.get("POCKETLEDGER_DB", _DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL,
    description  TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    date         TEXT    NOT NULL
)
"""


def init_db() -> None:
    """Create the transactions table if it doesn't already exist."""
    with get_connection() as conn:
        conn.execute(_CREATE_TABLE)
        conn.commit()


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def add_transaction(
    amount: Decimal, description: str, category: str, date: str
) -> int:
    """Insert a transaction and return the new row id.

    ``amount`` is converted to integer cents before storage.
    """
    amount_cents = int(amount * 100)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO transactions (amount_cents, description, category, date)"
            " VALUES (?, ?, ?, ?)",
            (amount_cents, description, category, date),
        )
        conn.commit()
        return cursor.lastrowid


def delete_transaction(tx_id: int) -> bool:
    """Delete a transaction by id. Returns False if the row did not exist."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM transactions WHERE id = ?", (tx_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def list_transactions() -> list[sqlite3.Row]:
    """Return all transactions ordered newest first (date DESC, id DESC)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, amount_cents, description, category, date"
            " FROM transactions"
            " ORDER BY date DESC, id DESC"
        ).fetchall()


def get_balance() -> int:
    """Return the sum of all amount_cents, or 0 if the table is empty."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions"
        ).fetchone()
        return row["total"]


def get_category_totals() -> list[dict]:
    """Return per-category totals ordered by total descending.

    Each element is a dict with keys ``category`` and ``total_cents``.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT category, SUM(amount_cents) AS total_cents"
            " FROM transactions"
            " GROUP BY category"
            " ORDER BY total_cents DESC"
        ).fetchall()
        return [{"category": r["category"], "total_cents": r["total_cents"]} for r in rows]
