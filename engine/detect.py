"""[2] DETECT — Bandit + gitleaks (+ Semgrep) findings, plus LLM logic-bug detection."""


def run_bandit(path: str):
    raise NotImplementedError


def run_gitleaks(path: str):
    raise NotImplementedError


def detect_logic_bugs(diff: str):
    """LLM-based detection for things static tools miss (e.g. race conditions)."""
    raise NotImplementedError
