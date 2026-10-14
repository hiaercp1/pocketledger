from fastapi import FastAPI

app = FastAPI(title="PocketLedger")


@app.get("/health")
def health():
    return {"status": "ok"}
