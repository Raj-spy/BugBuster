"""Branch, commit, and PR creation via git + GitHub REST API (PAT-based)."""


def create_branch(name: str):
    raise NotImplementedError


def commit_and_push(branch: str, files: list[str], message: str):
    raise NotImplementedError


def open_pull_request(branch: str, title: str, body: str):
    raise NotImplementedError
