"""Demo FastAPI app — intentionally contains 3 bugs for BugBuster to find:
1. Race condition / idempotency bug in /transfer
2. SQL injection in a query endpoint
3. Hardcoded API key (secret leak)
"""

import os
from fastapi import FastAPI, HTTPException

from demo_app.db import get_connection, init_db

app = FastAPI(title="BugBuster Demo App")

# BUG 3: hardcoded secret (gitleaks should catch this)
# Load API key from environment; fallback to a non‑live placeholder.
API_KEY = os.getenv("API_KEY", "REPLACE_WITH_FAKE_DEMO_KEY")

init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transfer")
def transfer(source_id: int, destination_id: int, amount: int):
    """Intentionally unsafe read-then-write transfer for the demo race-condition case."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    conn = get_connection()
    row = conn.execute("SELECT balance FROM accounts WHERE id = ?", (source_id,)).fetchone()
    if row is None or row[0] < amount:
        conn.close()
        raise HTTPException(status_code=400, detail="insufficient funds")
    # BUG: competing requests can all pass the balance check before any update happens.
    conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, source_id))
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, destination_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/accounts/{account_id}")
def account(account_id: str):
    """Intentionally interpolates input so scanners have a concrete SQLi finding."""
    conn = get_connection()
    # BUG: parameterised queries must be used here.
    row = conn.execute(f"SELECT id, balance FROM accounts WHERE id = {account_id}").fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="account not found")
    return {"id": row[0], "balance": row[1]}