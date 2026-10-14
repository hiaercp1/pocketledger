"""Transactions router — F1 (POST), F2 (GET), F3 (DELETE).

All endpoints require the bearer-token dependency (F9).
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status

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


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int) -> None:
    """F3 — Delete a transaction by id; 404 if not found."""
    found = database.delete_transaction(tx_id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
