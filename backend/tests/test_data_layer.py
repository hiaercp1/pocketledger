"""Data-layer unit tests for PocketLedger.

Each test gets its own isolated SQLite database via the ``db`` fixture, which
patches ``POCKETLEDGER_DB`` to a temporary file and tears it down afterwards.
No production DB is touched.
"""

import os
from decimal import Decimal

import pytest

import database


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Provide an isolated, initialised database for each test."""
    db_file = str(tmp_path / "test_ledger.db")
    monkeypatch.setenv("POCKETLEDGER_DB", db_file)
    database.init_db()
    yield db_file


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_add_and_retrieve_transaction(db):
    """add_transaction inserts a row that list_transactions returns."""
    tx_id = database.add_transaction(
        Decimal("42.50"), "Coffee", "Food", "2024-03-01"
    )
    assert isinstance(tx_id, int)
    assert tx_id > 0

    rows = database.list_transactions()
    assert len(rows) == 1
    assert rows[0]["id"] == tx_id
    assert rows[0]["amount_cents"] == 4250
    assert rows[0]["description"] == "Coffee"
    assert rows[0]["category"] == "Food"
    assert rows[0]["date"] == "2024-03-01"


def test_list_transactions_newest_first(db):
    """list_transactions returns rows ordered by date DESC, id DESC."""
    database.add_transaction(Decimal("10.00"), "Old", "A", "2024-01-01")
    database.add_transaction(Decimal("20.00"), "New", "A", "2024-06-15")
    database.add_transaction(Decimal("30.00"), "Same day later", "A", "2024-06-15")

    rows = database.list_transactions()
    assert rows[0]["date"] == "2024-06-15"
    assert rows[1]["date"] == "2024-06-15"
    # Within the same date the later-inserted row comes first (id DESC)
    assert rows[0]["id"] > rows[1]["id"]
    assert rows[2]["date"] == "2024-01-01"


def test_delete_existing_returns_true(db):
    """delete_transaction returns True when the row existed."""
    tx_id = database.add_transaction(
        Decimal("5.00"), "Test", "Cat", "2024-05-10"
    )
    result = database.delete_transaction(tx_id)
    assert result is True
    assert database.list_transactions() == []


def test_delete_nonexistent_returns_false(db):
    """delete_transaction returns False for an id that doesn't exist."""
    result = database.delete_transaction(99999)
    assert result is False


def test_get_balance_sum(db):
    """get_balance returns the correct signed sum of all amount_cents."""
    database.add_transaction(Decimal("100.00"), "Income", "Income", "2024-01-01")
    database.add_transaction(Decimal("-30.00"), "Expense", "Food", "2024-01-02")
    database.add_transaction(Decimal("50.50"), "Income2", "Income", "2024-01-03")

    # 10000 - 3000 + 5050 = 12050 cents
    assert database.get_balance() == 12050


def test_get_balance_empty_db(db):
    """get_balance returns 0 when there are no transactions."""
    assert database.get_balance() == 0


def test_get_category_totals_aggregation(db):
    """get_category_totals groups and sums correctly across multiple categories."""
    database.add_transaction(Decimal("50.00"), "a", "Food", "2024-01-01")
    database.add_transaction(Decimal("25.00"), "b", "Food", "2024-01-02")
    database.add_transaction(Decimal("200.00"), "c", "Travel", "2024-01-03")
    database.add_transaction(Decimal("-10.00"), "d", "Food", "2024-01-04")

    totals = database.get_category_totals()

    by_cat = {t["category"]: t["total_cents"] for t in totals}
    # Food: 5000 + 2500 - 1000 = 6500
    assert by_cat["Food"] == 6500
    # Travel: 20000
    assert by_cat["Travel"] == 20000
    # Travel has the highest total so it should be first
    assert totals[0]["category"] == "Travel"


def test_decimal_to_cents_conversion(db):
    """Fractional amounts are stored as exact integer cents without float rounding."""
    # This amount is a classic IEEE 754 trap: 0.1 + 0.2 != 0.3 in floats.
    database.add_transaction(Decimal("0.10"), "tiny1", "X", "2024-01-01")
    database.add_transaction(Decimal("0.20"), "tiny2", "X", "2024-01-02")

    assert database.get_balance() == 30  # 10 + 20 cents, exactly
