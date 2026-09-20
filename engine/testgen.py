"""[4] TEST — LLM generates a pytest that reproduces the bug.
Must FAIL on old code (red), stably, for the right reason.
"""


def generate_test(bug_report: dict) -> str:
    raise NotImplementedError


def run_red_check(test_code: str, repeat: int = 3) -> bool:
    """Run the generated test against the OLD code `repeat` times; must fail every time."""
    raise NotImplementedError
