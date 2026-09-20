"""Branch, commit, and PR creation via git + GitHub REST API (PAT-based)."""

import os
import subprocess
from pathlib import Path

import requests


def _ensure_git_user():
    """Ensure git user name and email are configured for automated commits."""
    try:
        proc = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, check=False)
        if not proc.stdout.strip():
            subprocess.run(["git", "config", "user.name", "BugBuster Bot"], check=False)
            subprocess.run(["git", "config", "user.email", "bot@bugbuster.local"], check=False)
    except Exception:
        pass


def create_branch(name: str) -> str:
    # Check if branch exists
    proc = subprocess.run(["git", "checkout", "-b", name], capture_output=True, text=True, check=False)
    if proc.returncode != 0 and "already exists" in proc.stderr:
        subprocess.run(["git", "checkout", name], check=False)
    return name


def commit_and_push(branch: str, files: list[str], message: str) -> bool:
    _ensure_git_user()
    subprocess.run(["git", "add", "--", *files], check=False)
    subprocess.run(["git", "commit", "-m", message], check=False)
    token = os.getenv("BOT_PAT")
    if token:
        proc = subprocess.run(["git", "push", "-u", "origin", branch], capture_output=True, text=True, check=False)
        return proc.returncode == 0
    return False


def open_pull_request(branch: str, title: str, body: str) -> str | None:
    token = os.getenv("BOT_PAT")
    repository = os.getenv("GITHUB_REPOSITORY")
    if not token or not repository:
        return None
    try:
        response = requests.post(
            f"https://api.github.com/repos/{repository}/pulls",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"title": title, "head": branch, "base": "main", "body": body},
            timeout=20,
        )
        if response.status_code == 201:
            return response.json().get("html_url")
        # If PR already exists
        if response.status_code == 422:
            return f"https://github.com/{repository}/pulls (already exists)"
    except Exception:
        pass
    return None


def safe_handle_proven_fix(
    branch_name: str,
    modified_files: list[str],
    title: str,
    report_markdown: str,
) -> dict:
    """Commit verified fix and attempt to open a PR if GitHub secrets are configured."""
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=False
    ).stdout.strip()
    create_branch(branch_name)
    pushed = commit_and_push(branch_name, modified_files, f"fix(bugbuster): {title} [verified]")
    pr_url = open_pull_request(branch_name, f"Fix: {title}", report_markdown) if pushed else None
    # Switch back to caller's original working branch
    if current_branch and current_branch != branch_name:
        subprocess.run(["git", "checkout", current_branch], check=False)
    return {
        "branch": branch_name,
        "committed": True,
        "pushed": pushed,
        "pr_url": pr_url,
    }
