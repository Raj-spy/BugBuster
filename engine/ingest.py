"""[1] INGEST — fetch a diff and identify its affected files."""

import re
import subprocess
from pathlib import Path

from engine.models import IngestedChange


def _files(diff: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)))


def ingest_from_pr(pr_url: str):
    """Fetch a public GitHub PR diff without requiring the gh CLI."""
    import requests

    response = requests.get(f"{pr_url.rstrip('/')}.diff", timeout=20)
    response.raise_for_status()
    diff = response.text
    return IngestedChange(source=pr_url, diff=diff, changed_files=_files(diff))


def ingest_from_repo(repo_url: str):
    # The caller is expected to run in the checked-out repository.
    completed = subprocess.run(
        ["git", "diff", "HEAD~1", "HEAD"], capture_output=True, text=True, check=False
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "Could not read repository diff")
    return IngestedChange(source=repo_url, diff=completed.stdout, changed_files=_files(completed.stdout))


def ingest_from_diff(diff_path: str):
    path = Path(diff_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    diff = path.read_text(encoding="utf-8")
    return IngestedChange(source=str(path), diff=diff, changed_files=_files(diff), root=Path.cwd())
