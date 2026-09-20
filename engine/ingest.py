"""[1] INGEST — fetch diff / changed files from PR, repo, or a .patch file."""


def ingest_from_pr(pr_url: str):
    raise NotImplementedError


def ingest_from_repo(repo_url: str):
    raise NotImplementedError


def ingest_from_diff(diff_path: str):
    raise NotImplementedError
