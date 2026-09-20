"""[4] TEST — LLM generates a pytest that reproduces the bug.
Must FAIL on old code (red), stably, for the right reason.
"""

import subprocess
import tempfile
from pathlib import Path


def generate_test(bug_report: dict) -> str:
    """Return a bounded pytest template; production callers may replace it with LLM output."""
    rule = bug_report.get("rule_id", "")
    if rule == "read-write-race":
        return """def test_transfer_is_atomic():\n    # Fill in an app-specific concurrent reproduction.\n    assert False, 'BugBuster must replace this template with a reproducer'\n"""
    return """def test_security_finding_is_fixed():\n    assert False, 'BugBuster must replace this template with a reproducer'\n"""


def run_red_check(test_code: str, repeat: int = 3) -> bool:
    """Run the generated test against the OLD code `repeat` times; must fail every time."""
    with tempfile.TemporaryDirectory() as directory:
        test_path = Path(directory) / "test_generated.py"
        test_path.write_text(test_code, encoding="utf-8")
        outcomes = [subprocess.run(["python", "-m", "pytest", "-q", str(test_path)], capture_output=True).returncode
                    for _ in range(repeat)]
    return outcomes == [1] * repeat
