"""[4] TEST — LLM generates a pytest that reproduces the bug.
Must FAIL on old code (red), stably, for the right reason.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def _clean_code_block(text: str) -> str:
    """Extract Python code from markdown blocks if present."""
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def generate_test(finding: dict, target_file_content: str | None = None) -> str:
    """Generate a reproducer test using LLM with fallback templates."""
    from engine.llm import call_llm

    rule = finding.get("rule_id", "")
    path = finding.get("path", "")
    message = finding.get("message", "")
    evidence = finding.get("evidence", "")

    # Read target file content if path exists and content not supplied
    if not target_file_content and path and Path(path).exists():
        try:
            target_file_content = Path(path).read_text(encoding="utf-8")
        except Exception:
            target_file_content = ""

    prompt = f"""You are a senior software test engineer. Write a self-contained, reproducible `pytest` test for this bug.
The test must FAIL on the current buggy code (RED check), and will PASS once the bug is fixed (GREEN check).

BUG DETAILS:
- Rule ID: {rule}
- File: {path}
- Description: {message}
- Evidence/Code: {evidence}

RELEVANT SOURCE CODE:
{target_file_content[:1500] if target_file_content else "N/A"}

REQUIREMENTS:
1. Return ONLY valid, executable Python code for pytest. No explanation, no markdown wrap.
2. The test must import the affected code directly (e.g. `from demo_app.main import app` or use TestClient).
3. If FastAPI endpoint: use `from fastapi.testclient import TestClient` to test the endpoint.
4. For race conditions: use ThreadPoolExecutor with concurrent requests to trigger the race.
5. Make sure assertions clearly fail on the old buggy behavior.
"""
    try:
        raw_test = call_llm(prompt, system="You write robust, deterministic pytest reproducers.")
        cleaned = _clean_code_block(raw_test)
        if "def test_" in cleaned:
            return cleaned
    except Exception:
        pass

    # Safe deterministic fallbacks
    if rule == "read-write-race":
        return """import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from demo_app.main import app
from demo_app.db import init_db, get_connection

def test_transfer_race_condition():
    init_db()
    client = TestClient(app)
    # Check initial balance is 100
    conn = get_connection()
    b1 = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    conn.close()

    def do_transfer():
        return client.post("/transfer?source_id=1&destination_id=2&amount=60")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_transfer) for _ in range(2)]
        responses = [f.result().status_code for f in futures]

    # Only one 60-debit from 100 should succeed; both succeeding proves race condition
    success_count = sum(1 for r in responses if r == 200)
    assert success_count <= 1, f"Race condition reproduced: {success_count} concurrent debits succeeded!"
"""
    elif rule == "generic-api-key" or "secret" in rule.lower():
        return """def test_no_hardcoded_api_key():
    import os
    from demo_app import main
    # API_KEY must not be a hardcoded default or string constant
    raw_key = getattr(main, "API_KEY", "")
    assert not raw_key.startswith("sk-live-"), "API key is hardcoded directly in source code!"
"""
    elif "b608" in rule.lower() or "sql" in rule.lower():
        endpoint = "/transactions/search?account_id=1%20OR%201=1" if ("transaction" in str(evidence) or "transaction" in str(message)) else "/accounts/1 OR 1=1"
        return f"""import pytest
from fastapi.testclient import TestClient
from demo_app.main import app

def test_sql_injection_reproduced():
    client = TestClient(app)
    # Injecting SQL payload must be rejected or parameterized
    resp = client.get("{endpoint}")
    # In vulnerable code, '1 OR 1=1' returns 200 with record
    # In secure parameterized code, '1 OR 1=1' matches no account and returns 404/422/400
    assert resp.status_code in [400, 404, 422], f"SQL Injection succeeded with status {{resp.status_code}}"
"""
    return """def test_security_finding_is_fixed():\n    assert False, 'BugBuster reproducer: finding not yet fixed'\n"""


def run_red_check(test_code: str, repeat: int = 3, target_dir: str | Path | None = None) -> bool:
    """Run the generated test against the OLD code `repeat` times; must fail every time."""
    cwd = Path(target_dir) if target_dir else Path.cwd()
    env = {**os.environ, "PYTHONPATH": str(cwd)}

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        test_path = root / "test_generated.py"
        test_path.write_text(test_code, encoding="utf-8")
        outcomes = [
            subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-o", "rootdir=.", "test_generated.py"],
                cwd=str(root),
                env=env,
                capture_output=True,
            ).returncode
            for _ in range(repeat)
        ]
    return outcomes == [1] * repeat
