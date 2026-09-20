"""Generate proof report (markdown + JSON) for a bug/fix run."""


def build_report(bug_report: dict, test_result: dict, verify_result: dict) -> dict:
    raise NotImplementedError


def to_markdown(report: dict) -> str:
    raise NotImplementedError
