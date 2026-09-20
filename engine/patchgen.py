"""[5] PATCH — generate fix candidates from 2 LLMs, pick the smaller diff."""


def generate_patch_candidates(bug_report: dict, test_code: str) -> list[str]:
    raise NotImplementedError


def choose_smallest_diff(candidates: list[str]) -> str:
    raise NotImplementedError
