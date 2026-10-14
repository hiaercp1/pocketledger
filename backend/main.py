"""PocketLedger — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from auth import verify_token
from routers import summary, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    database.init_db()
    yield


app = FastAPI(title="PocketLedger", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(summary.router)


@app.get("/health")
def health(_: None = Depends(verify_token)):
    return {"status": "ok"}
