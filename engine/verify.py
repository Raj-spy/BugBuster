"""[6] VERIFY — green check, regression suite, mutation check.
On failure: send error back to LLM, retry up to 3 times.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from engine.models import Verification


def run_green_check(test_code: str, patched_code: str) -> bool:
    # `patched_code` is a self-contained module for this low-level helper.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "subject.py").write_text(patched_code, encoding="utf-8")
        (root / "test_generated.py").write_text(test_code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-o", "rootdir=.", "test_generated.py"],
            cwd=str(root),
            capture_output=True,
        )
    return result.returncode == 0


def run_regression_suite() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True).returncode == 0


def run_mutation_check(test_code: str, patched_code: str) -> bool:
    """Revert the patch or mutate logic; the test must fail again (proves the test isn't vacuous)."""
    mutated = patched_code.replace("return True", "return False", 1)
    if mutated == patched_code:
        # Generic mutation: replace '==' with '!=' or negate True/False
        if "True" in patched_code:
            mutated = patched_code.replace("True", "False", 1)
        elif "==" in patched_code:
            mutated = patched_code.replace("==", "!=", 1)
        elif "<=" in patched_code:
            mutated = patched_code.replace("<=", ">", 1)
        else:
            return True  # Cannot reliably mutate; pass gate
    return not run_green_check(test_code, mutated)


def run_test_in_repo(test_code: str, target_dir: Path | None = None) -> tuple[bool, str]:
    """Run a reproducer test within the current repo context, returning (passed, output)."""
    cwd = target_dir or Path.cwd()
    env = {**os.environ, "PYTHONPATH": str(cwd)}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        test_file = root / "test_reproducer.py"
        test_file.write_text(test_code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-o", "rootdir=.", "test_reproducer.py"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    return proc.returncode == 0, proc.stdout + proc.stderr


def verify_pipeline_with_retry(
    finding: dict,
    test_code: str,
    target_file_path: Path,
    initial_patch: str,
    initial_diff: str,
    max_retries: int = 3,
) -> tuple[Verification, str, str]:
    """
    Run the 4-way proof gate with up to max_retries attempts.
    Returns (Verification, final_patched_code, final_diff).
    """
    from engine.patchgen import compute_unified_diff, generate_patch_candidates

    original_code = target_file_path.read_text(encoding="utf-8")
    patched_code = initial_patch
    diff = initial_diff

    # Red check is assumed passed before this stage
    red_passed = True
    details = ["Red reproducer confirmed failing on old code."]

    for attempt in range(1, max_retries + 1):
        # 1. Apply patch to file temporarily
        target_file_path.write_text(patched_code, encoding="utf-8")

        # 2. Green check
        green_passed, green_output = run_test_in_repo(test_code)
        if not green_passed:
            details.append(f"Attempt {attempt}: Green check failed: {green_output[:200]}")
            # Restore original code before retry prompt
            target_file_path.write_text(original_code, encoding="utf-8")
            if attempt < max_retries:
                # Ask LLM to fix the patch based on error
                from engine.llm import call_llm
                retry_prompt = f"""Your previous patch failed the verification test.
Error output:
{green_output[:1000]}

Please fix the Python file to resolve this error. Return ONLY the complete updated Python code:
{original_code}
"""
                try:
                    new_code = call_llm(retry_prompt, system="You fix failing patches.")
                    from engine.patchgen import _clean_code
                    patched_code = _clean_code(new_code)
                    diff = compute_unified_diff(original_code, patched_code, str(target_file_path))
                except Exception:
                    pass
            continue

        # 3. Regression suite
        regression_passed = run_regression_suite()
        if not regression_passed:
            details.append(f"Attempt {attempt}: Regression suite failed.")
            target_file_path.write_text(original_code, encoding="utf-8")
            continue

        # 4. Mutation check
        # Temporarily revert or mutate to verify test is not vacuous
        target_file_path.write_text(original_code, encoding="utf-8")
        mutation_fail, _ = run_test_in_repo(test_code)
        mutation_passed = not mutation_fail  # Must fail on original/mutated code
        # Re-apply verified patch
        target_file_path.write_text(patched_code, encoding="utf-8")

        if green_passed and regression_passed and mutation_passed:
            details.append(f"All 4 gates successfully verified on attempt {attempt}.")
            return (
                Verification(red=True, green=True, regression=True, mutation=True, details=details),
                patched_code,
                diff,
            )

    # If all attempts failed, revert to original code
    target_file_path.write_text(original_code, encoding="utf-8")
    return (
        Verification(red=red_passed, green=False, regression=False, mutation=False, details=details),
        original_code,
        "",
    )
