"""Branch, commit, and PR creation via git + GitHub REST API (PAT-based)."""

import os
import subprocess

import requests


def create_branch(name: str):
    subprocess.run(["git", "checkout", "-b", name], check=True)
    return name


def commit_and_push(branch: str, files: list[str], message: str):
    subprocess.run(["git", "add", "--", *files], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)


def open_pull_request(branch: str, title: str, body: str):
    token = os.getenv("BOT_PAT")
    repository = os.getenv("GITHUB_REPOSITORY")
    if not token or not repository:
        raise RuntimeError("BOT_PAT and GITHUB_REPOSITORY are required to open a PR")
    response = requests.post(f"https://api.github.com/repos/{repository}/pulls",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"title": title, "head": branch, "base": "main", "body": body}, timeout=20)
    response.raise_for_status()
    return response.json()["html_url"]
