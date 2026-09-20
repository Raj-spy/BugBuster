"""Demo FastAPI app — intentionally contains 3 bugs for BugBuster to find:
1. Race condition / idempotency bug in /transfer
2. SQL injection in a query endpoint
3. Hardcoded API key (secret leak)
"""

from fastapi import FastAPI

app = FastAPI(title="BugBuster Demo App")

# BUG 3: hardcoded secret (gitleaks should catch this)
API_KEY = "sk-live-REPLACE_WITH_FAKE_DEMO_KEY_1234567890"


@app.get("/health")
def health():
    return {"status": "ok"}


# TODO: /transfer endpoint (race condition bug) goes here
# TODO: SQL injection endpoint goes here
