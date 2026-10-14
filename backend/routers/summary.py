"""Summary router — F5 (GET /summary/categories) and balance.

All endpoints require the bearer-token dependency (F9).
"""

from decimal import Decimal

from fastapi import APIRouter, Depends

import database
from auth import verify_token
from models import BalanceResponse, CategoryTotal

router = APIRouter(
    prefix="/summary",
    tags=["summary"],
    dependencies=[Depends(verify_token)],
)


@router.get("/balance", response_model=BalanceResponse)
def get_balance() -> BalanceResponse:
    """Return the current ledger balance."""
    cents = database.get_balance()
    return BalanceResponse(balance=Decimal(cents) / 100)


@router.get("/categories", response_model=list[CategoryTotal])
def get_category_totals() -> list[CategoryTotal]:
    """F5 — Return per-category aggregated totals plus implicit balance."""
    rows = database.get_category_totals()
    return [
        CategoryTotal(
            category=row["category"],
            total=Decimal(row["total_cents"]) / 100,
        )
        for row in rows
    ]
