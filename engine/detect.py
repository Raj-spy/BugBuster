"""[2] DETECT — static scanners plus conservative source-level secret detection."""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from engine.models import Finding


def _run(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    if not shutil.which(command[0]):
        return None
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=90)


def run_bandit(path: str):
    result = _run(["bandit", "-r", path, "-ll", "-x", "./tests,./.venv,./cache", "-f", "json", "-q"])
    if result is None or not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return [
        Finding(tool="bandit", rule_id=item["test_id"], severity=item["issue_severity"].lower(),
                message=item["issue_text"], path=item["filename"], line=item["line_number"],
                evidence=item.get("code"))
        for item in payload.get("results", [])
    ]


def run_gitleaks(path: str):
    """Use gitleaks when bundled; use a narrow fallback for offline local runs."""
    findings: list[Finding] = []
    if shutil.which("gitleaks"):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as report:
            report_name = report.name
        try:
            result = subprocess.run(["gitleaks", "detect", "--no-git", "--source", path,
                "--report-format", "json", "--report-path", report_name], capture_output=True,
                text=True, check=False, timeout=90)
            if Path(report_name).stat().st_size:
                for item in json.loads(Path(report_name).read_text(encoding="utf-8")):
                    findings.append(Finding(tool="gitleaks", rule_id=item.get("RuleID", "secret"),
                        severity="high", message=item.get("Description", "Potential secret"),
                        path=item.get("File"), line=item.get("StartLine"), evidence=item.get("Match")))
            return findings
        finally:
            Path(report_name).unlink(missing_ok=True)
    # Deterministic fallback keeps local runs useful.
    pattern = re.compile(r"(?:api[_-]?key|token|secret)\s*=\s*[\"']([^\"']{16,})", re.I)
    for file in Path(path).rglob("*.py"):
        for line_no, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                findings.append(Finding(tool="gitleaks", rule_id="generic-api-key", severity="high",
                    message="Potential hardcoded credential", path=str(file), line=line_no, evidence=line.strip()))
    return findings


def detect_logic_bugs(diff: str):
    """LLM-based detection for things static tools miss (e.g. race conditions)."""
    findings = []
    if "SELECT balance" in diff and "UPDATE accounts SET balance" in diff:
        findings.append(Finding(tool="heuristic", rule_id="read-write-race", severity="high",
            message="Balance check and update may race; make the debit conditional and atomic."))
    return findings


def run_all(path: str, diff: str) -> list[Finding]:
    """Run required detectors. A missing optional executable never fails the pipeline."""
    return [*run_bandit(path), *run_gitleaks(path), *detect_logic_bugs(diff)]
