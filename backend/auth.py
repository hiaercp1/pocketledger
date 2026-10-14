"""Bearer-token authentication dependency for PocketLedger.

The expected token is read from the ``POCKETLEDGER_TOKEN`` environment
variable **at request time** so changes to the env take effect without a
restart and tests can patch it freely.

Usage::

    @router.get("/some-route")
    def handler(_: None = Depends(verify_token)):
        ...
"""

import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """Raise HTTP 401 when the bearer token is missing or wrong."""
    expected = os.environ.get("POCKETLEDGER_TOKEN", "")
    token = credentials.credentials if credentials else ""
    # Both sides must be non-empty and match; compare_digest prevents
    # timing-based token enumeration.
    if not expected or not token or not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
