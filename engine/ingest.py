"""[1] INGEST — fetch a diff and identify its affected files."""

import re
import subprocess
from pathlib import Path

from engine.models import IngestedChange


def _files(diff: str) -> list[str]:
    return list(dict.fromkeys(f.strip() for f in re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)))



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
        ["git", "diff", "HEAD~1", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "Could not read repository diff")
    diff_text = completed.stdout or ""
    return IngestedChange(source=repo_url, diff=diff_text, changed_files=_files(diff_text))


def ingest_from_diff(diff_path: str):
    path = Path(diff_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    raw_bytes = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "cp1252"):
        try:
            diff = raw_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        diff = raw_bytes.decode("utf-8", errors="replace")
    return IngestedChange(source=str(path), diff=diff, changed_files=_files(diff), root=Path.cwd())

