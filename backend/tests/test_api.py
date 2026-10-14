"""API integration tests using FastAPI TestClient.

Covers authentication (F9) and the core CRUD + summary endpoints.
Each test uses an isolated temp DB so no production data is touched.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import database
import main as app_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Return a TestClient wired to an isolated DB and a known token."""
    db_file = str(tmp_path / "api_test_ledger.db")
    monkeypatch.setenv("POCKETLEDGER_DB", db_file)
    monkeypatch.setenv("POCKETLEDGER_TOKEN", "test-token")
    # Re-initialise the DB for this test's path
    database.init_db()
    with TestClient(app_module.app) as tc:
        yield tc


TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


# ---------------------------------------------------------------------------
# Auth tests (F9)
# ---------------------------------------------------------------------------


def test_401_without_token(client):
    """Every business endpoint returns 401 when no token is provided."""
    assert client.get("/transactions").status_code == 401


def test_health_401_without_token(client):
    """GET /health returns 401 when no bearer token is provided."""
    assert client.get("/health").status_code == 401


def test_401_wrong_token(client):
    """A wrong token is also rejected."""
    assert client.get("/transactions", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_401_post_without_token(client):
    """POST /transactions returns 401 without a token."""
    payload = {"amount": "10.00", "description": "x", "category": "y", "date": "2024-01-01"}
    assert client.post("/transactions", json=payload).status_code == 401


def test_401_delete_without_token(client):
    """DELETE /transactions/{id} returns 401 without a token."""
    assert client.delete("/transactions/1").status_code == 401


def test_401_categories_without_token(client):
    """GET /summary/categories returns 401 without a token."""
    assert client.get("/summary/categories").status_code == 401


# ---------------------------------------------------------------------------
# F1 — POST /transactions
# ---------------------------------------------------------------------------


def test_create_transaction_returns_201(client):
    """POST /transactions creates a row and returns 201 with the new id."""
    payload = {"amount": "25.50", "description": "Lunch", "category": "Food", "date": "2024-03-15"}
    resp = client.post("/transactions", json=payload, headers=AUTH)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["amount"] == "25.50"
    assert body["description"] == "Lunch"
    assert body["category"] == "Food"
    assert body["date"] == "2024-03-15"


def test_create_transaction_invalid_amount(client):
    """POST /transactions rejects a zero amount with 422."""
    payload = {"amount": "0", "description": "Bad", "category": "X", "date": "2024-01-01"}
    assert client.post("/transactions", json=payload, headers=AUTH).status_code == 422


# ---------------------------------------------------------------------------
# F2 — GET /transactions
# ---------------------------------------------------------------------------


def test_list_transactions_empty(client):
    """GET /transactions returns an empty list when DB is empty."""
    resp = client.get("/transactions", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_transactions_order(client):
    """GET /transactions returns newest date first."""
    client.post("/transactions", json={"amount": "10.00", "description": "Old", "category": "A", "date": "2024-01-01"}, headers=AUTH)
    client.post("/transactions", json={"amount": "20.00", "description": "New", "category": "A", "date": "2024-06-01"}, headers=AUTH)
    rows = client.get("/transactions", headers=AUTH).json()
    assert rows[0]["date"] == "2024-06-01"
    assert rows[1]["date"] == "2024-01-01"


# ---------------------------------------------------------------------------
# F3 — DELETE /transactions/{id}
# ---------------------------------------------------------------------------


def test_delete_existing_returns_204(client):
    """DELETE /transactions/{id} returns 204 when the row exists."""
    resp = client.post("/transactions", json={"amount": "5.00", "description": "X", "category": "Y", "date": "2024-05-01"}, headers=AUTH)
    tx_id = resp.json()["id"]
    assert client.delete(f"/transactions/{tx_id}", headers=AUTH).status_code == 204


def test_delete_nonexistent_returns_404(client):
    """DELETE /transactions/{id} returns 404 when the row does not exist."""
    assert client.delete("/transactions/99999", headers=AUTH).status_code == 404


# ---------------------------------------------------------------------------
# F5 — GET /summary/categories
# ---------------------------------------------------------------------------


def test_summary_categories_aggregation(client):
    """GET /summary/categories returns grouped totals as Decimal strings."""
    client.post("/transactions", json={"amount": "100.00", "description": "a", "category": "Income", "date": "2024-01-01"}, headers=AUTH)
    client.post("/transactions", json={"amount": "-30.00", "description": "b", "category": "Food", "date": "2024-01-02"}, headers=AUTH)
    client.post("/transactions", json={"amount": "50.00", "description": "c", "category": "Income", "date": "2024-01-03"}, headers=AUTH)

    resp = client.get("/summary/categories", headers=AUTH)
    assert resp.status_code == 200
    totals = {row["category"]: row["total"] for row in resp.json()}
    assert Decimal(totals["Income"]) == Decimal("150.00")
    assert Decimal(totals["Food"]) == Decimal("-30.00")


# ---------------------------------------------------------------------------
# Balance endpoint
# ---------------------------------------------------------------------------


def test_balance_endpoint(client):
    """GET /summary/balance returns correct balance as a Decimal string."""
    client.post("/transactions", json={"amount": "200.00", "description": "pay", "category": "Income", "date": "2024-01-01"}, headers=AUTH)
    client.post("/transactions", json={"amount": "-50.00", "description": "rent", "category": "Housing", "date": "2024-01-02"}, headers=AUTH)
    resp = client.get("/summary/balance", headers=AUTH)
    assert resp.status_code == 200
    assert Decimal(resp.json()["balance"]) == Decimal("150.00")


# ---------------------------------------------------------------------------
# F8 — GET /transactions/export (CSV)
# ---------------------------------------------------------------------------


def test_export_csv_401_without_token(client):
    """GET /transactions/export returns 401 when no bearer token is provided."""
    assert client.get("/transactions/export").status_code == 401


def test_export_csv_header_row(client):
    """GET /transactions/export always returns the header row, even when empty."""
    resp = client.get("/transactions/export", headers=AUTH)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    lines = resp.text.splitlines()
    assert lines[0] == "id,date,description,category,amount"


def test_export_csv_content(client):
    """GET /transactions/export returns one data row per transaction, newest first."""
    client.post(
        "/transactions",
        json={"amount": "100.00", "description": "Salary", "category": "Income", "date": "2024-01-01"},
        headers=AUTH,
    )
    client.post(
        "/transactions",
        json={"amount": "-25.50", "description": "Groceries", "category": "Food", "date": "2024-06-15"},
        headers=AUTH,
    )
    resp = client.get("/transactions/export", headers=AUTH)
    assert resp.status_code == 200
    lines = resp.text.splitlines()
    # header + 2 data rows
    assert len(lines) == 3
    # newest first (2024-06-15)
    assert "Groceries" in lines[1]
    assert "-25.50" in lines[1]
    assert "Salary" in lines[2]
    assert "100.00" in lines[2]


def test_export_csv_amount_is_exact_decimal(client):
    """Amounts in the CSV are exact Decimal strings, not floats."""
    client.post(
        "/transactions",
        json={"amount": "9.99", "description": "Coffee", "category": "Food", "date": "2024-03-01"},
        headers=AUTH,
    )
    resp = client.get("/transactions/export", headers=AUTH)
    assert resp.status_code == 200
    # Must contain exactly two decimal places, not a float like 9.99000001 or bare 9.99 without trailing zero
    assert "9.99" in resp.text
    # Verify two-decimal-place format: parse the amount column from the data row
    lines = resp.text.splitlines()
    data_row = lines[1]
    amount_field = data_row.split(",")[-1]
    # Must match exactly N.NN format (two decimal places, no more, no less)
    import re
    assert re.match(r"^-?\d+\.\d{2}$", amount_field), f"Amount {amount_field!r} is not in two-decimal-place format"


def test_export_csv_content_disposition(client):
    """GET /transactions/export sets Content-Disposition to trigger a download."""
    resp = client.get("/transactions/export", headers=AUTH)
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert "transactions.csv" in resp.headers.get("content-disposition", "")
