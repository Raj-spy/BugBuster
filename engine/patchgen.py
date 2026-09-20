"""[5] PATCH — validate generated patches, generate clean diffs, and pick the minimal fix."""

import ast
import difflib
import re
from pathlib import Path


def _clean_code(text: str) -> str:
    """Extract Python code from markdown fences if present."""
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def compute_unified_diff(original: str, patched: str, file_path: str = "file.py") -> str:
    orig_lines = original.splitlines(keepends=True)
    patch_lines = patched.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        patch_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )
    return "".join(diff)


def generate_patch_candidates(
    finding: dict,
    test_code: str,
    original_code: str,
    file_path: str = "subject.py",
) -> list[tuple[str, str]]:
    """Return list of (patched_code, unified_diff) candidates."""
    from engine.llm import call_llm

    rule = finding.get("rule_id", "")
    msg = finding.get("message", "")

    prompt = f"""You are a principal security engineer. Fix the following bug in the Python file.
Do NOT break existing functionality. Make the minimal necessary change.

BUG FINDING:
- Rule ID: {rule}
- Description: {msg}

FAILING REPRODUCER TEST:
{test_code}

CURRENT CODE TO FIX:
{original_code}

INSTRUCTIONS:
Return ONLY the complete updated Python source code for this file.
No explanations, no markdown formatting (or within a single ```python block).
The code must be valid, executable Python syntax.
"""
    candidates: list[tuple[str, str]] = []

    # Attempt up to 2 distinct generations
    for _ in range(2):
        try:
            answer = call_llm(prompt, system="You write minimal, secure Python fixes.")
            cleaned = _clean_code(answer)
            # Verify Python syntax
            ast.parse(cleaned)
            diff = compute_unified_diff(original_code, cleaned, file_path)
            if diff.strip():
                candidates.append((cleaned, diff))
        except Exception:
            continue

    # Deterministic fallback patches for standard demo vulnerabilities
    if not candidates:
        fallback = _get_fallback_patch(rule, original_code)
        if fallback:
            diff = compute_unified_diff(original_code, fallback, file_path)
            candidates.append((fallback, diff))

    return candidates


def _get_fallback_patch(rule_id: str, code: str) -> str | None:
    if rule_id == "read-write-race":
        # Make the SQLite balance debit atomic: only update if balance >= amount
        old = 'conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, source_id))'
        new = (
            'cursor = conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?", (amount, source_id, amount))\n'
            '    if cursor.rowcount == 0:\n'
            '        conn.close()\n'
            '        raise HTTPException(status_code=400, detail="insufficient funds")'
        )
        if old in code:
            return code.replace(old, new)
    elif rule_id == "generic-api-key":
        old = 'API_KEY = "sk-live-REPLACE_WITH_FAKE_DEMO_KEY_1234567890"'
        new = 'import os\nAPI_KEY = os.getenv("DEMO_API_KEY", "")'
        if old in code:
            return code.replace(old, new)
    elif "sql" in rule_id.lower() or "b608" in rule_id.lower():
        patched = code
        if 'row = conn.execute(f"SELECT id, balance FROM accounts WHERE id = {account_id}").fetchone()' in patched:
            patched = patched.replace(
                'row = conn.execute(f"SELECT id, balance FROM accounts WHERE id = {account_id}").fetchone()',
                'row = conn.execute("SELECT id, balance FROM accounts WHERE id = ?", (account_id,)).fetchone()',
            )
        if 'query = f"SELECT id, balance FROM accounts WHERE id = {account_id}"' in patched:
            patched = patched.replace(
                'query = f"SELECT id, balance FROM accounts WHERE id = {account_id}"',
                'query = "SELECT id, balance FROM accounts WHERE id = ?"',
            )
            patched = patched.replace(
                'row = conn.execute(query).fetchone()',
                'row = conn.execute(query, (account_id,)).fetchone()',
            )
        if patched != code:
            return patched

    return None


def choose_smallest_diff(candidates: list[tuple[str, str]]) -> tuple[str, str]:
    if not candidates:
        raise ValueError("No valid patch candidates available")

    def diff_weight(item: tuple[str, str]) -> int:
        diff = item[1]
        return sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))

    return min(candidates, key=diff_weight)
