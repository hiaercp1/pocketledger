"""Transactions router — F1 (POST), F2 (GET), F3 (DELETE), F8 (CSV export).

All endpoints require the bearer-token dependency (F9).
"""

import csv
import io
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

import database
from auth import verify_token
from models import TransactionCreate, TransactionResponse

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(verify_token)],
)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate) -> TransactionResponse:
    """F1 — Add a new transaction."""
    tx_id = database.add_transaction(
        amount=body.amount,
        description=body.description,
        category=body.category,
        date=body.date,
    )
    return TransactionResponse(
        id=tx_id,
        amount=body.amount,
        description=body.description,
        category=body.category,
        date=body.date,
    )


@router.get("", response_model=list[TransactionResponse])
def list_transactions() -> list[TransactionResponse]:
    """F2 — List all transactions, newest first."""
    rows = database.list_transactions()
    return [
        TransactionResponse(
            id=row["id"],
            amount=Decimal(row["amount_cents"]) / 100,
            description=row["description"],
            category=row["category"],
            date=row["date"],
        )
        for row in rows
    ]


@router.get("/export")
def export_transactions_csv() -> StreamingResponse:
    """F8 — Export all transactions as a CSV file, newest first.

    Returns a ``text/csv`` response with a Content-Disposition attachment
    header so browsers trigger a file download.  Amounts are exact Decimal
    strings; the built-in ``csv`` module is used (no third-party deps).
    """
    rows = database.list_transactions()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "description", "category", "amount"])
    for row in rows:
        amount = str((Decimal(row["amount_cents"]) / 100).quantize(Decimal("0.01")))
        writer.writerow([row["id"], row["date"], row["description"], row["category"], amount])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int) -> None:
    """F3 — Delete a transaction by id; 404 if not found."""
    found = database.delete_transaction(tx_id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
