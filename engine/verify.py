"""[6] VERIFY — green check, regression suite, mutation check.
On failure: send error back to LLM, retry up to 3 times.
"""


def run_green_check(test_code: str, patched_code: str) -> bool:
    raise NotImplementedError


def run_regression_suite() -> bool:
    raise NotImplementedError


def run_mutation_check(test_code: str, patched_code: str) -> bool:
    """Revert the patch; the test must fail again (proves the test isn't vacuous)."""
    raise NotImplementedError
