"""Pydantic request/response models for PocketLedger.

Amounts are ``Decimal`` throughout Python and serialised as strings in JSON
responses to preserve precision across the JSON boundary.
"""

import re
from decimal import ROUND_DOWN, Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_ISO_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")

# Maximum absolute amount: 1 billion — avoids int overflow when stored as cents.
_MAX_AMOUNT = Decimal("1000000000")

_MAX_STR_LEN = 200


# ---------------------------------------------------------------------------
# Shared validator helpers
# ---------------------------------------------------------------------------


def _check_amount(v: Decimal) -> Decimal:
    """Raise ValueError if amount is zero, has >2 dp, or exceeds the sane bound."""
    if v == 0:
        raise ValueError("amount must not be zero")
    if abs(v) > _MAX_AMOUNT:
        raise ValueError(f"amount magnitude must not exceed {_MAX_AMOUNT}")
    quantised = v.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if quantised != v:
        raise ValueError("amount must have at most 2 decimal places")
    return v


def _check_date(v: str) -> str:
    if not _ISO_DATE_RE.match(v):
        raise ValueError("date must be in YYYY-MM-DD format")
    return v


def _check_nonempty(label: str, v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError(f"{label} must not be empty")
    return v


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class TransactionCreate(BaseModel):
    """Payload for creating a new transaction."""

    amount: Decimal
    description: str = Field(..., min_length=1, max_length=_MAX_STR_LEN)
    category: str = Field(..., min_length=1, max_length=_MAX_STR_LEN)
    date: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return _check_amount(v)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return _check_date(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return _check_nonempty("description", v)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return _check_nonempty("category", v)

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:  # noqa: PLR0201
        return str(v)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TransactionResponse(BaseModel):
    """A persisted transaction returned by the API."""

    id: int
    amount: Decimal
    description: str
    category: str
    date: str

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:  # noqa: PLR0201
        return str(v)


class BalanceResponse(BaseModel):
    """Current ledger balance."""

    balance: Decimal

    @field_serializer("balance")
    def serialize_balance(self, v: Decimal) -> str:  # noqa: PLR0201
        return str(v)


class CategoryTotal(BaseModel):
    """Aggregated total for a single category."""

    category: str
    total: Decimal

    @field_serializer("total")
    def serialize_total(self, v: Decimal) -> str:  # noqa: PLR0201
        return str(v)
