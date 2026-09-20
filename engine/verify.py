"""[6] VERIFY — green check, regression suite, mutation check.
On failure: send error back to LLM, retry up to 3 times.
"""

import subprocess
import tempfile
from pathlib import Path


def run_green_check(test_code: str, patched_code: str) -> bool:
    # `patched_code` is a self-contained module for this low-level helper.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "subject.py").write_text(patched_code, encoding="utf-8")
        (root / "test_generated.py").write_text(test_code, encoding="utf-8")
        result = subprocess.run(["python", "-m", "pytest", "-q", str(root / "test_generated.py")], capture_output=True)
    return result.returncode == 0


def run_regression_suite() -> bool:
    return subprocess.run(["python", "-m", "pytest", "-q"], capture_output=True).returncode == 0


def run_mutation_check(test_code: str, patched_code: str) -> bool:
    """Revert the patch; the test must fail again (proves the test isn't vacuous)."""
    # Mutation is meaningful only when the generated test imports `subject`.
    mutated = patched_code.replace("return True", "return False", 1)
    if mutated == patched_code:
        return False
    return not run_green_check(test_code, mutated)
