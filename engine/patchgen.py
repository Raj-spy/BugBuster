"""[5] PATCH — validate generated unified-diff candidates and pick the smallest."""

def generate_patch_candidates(bug_report: dict, test_code: str) -> list[str]:
    # Kept intentionally provider-agnostic: the orchestrator asks two configured models.
    from engine.llm import call_llm
    prompt = f"""Return only a unified git diff for this finding:\n{bug_report}\n\n"
                f"The failing pytest is:\n{test_code}\nKeep the change minimal."""
    candidates = []
    for _ in range(2):
        try:
            answer = call_llm(prompt, system="You write minimal, secure Python patches.")
            if "diff --git" in answer:
                candidates.append(answer[answer.index("diff --git"):])
        except RuntimeError:
            break
    return candidates


def choose_smallest_diff(candidates: list[str]) -> str:
    valid = [candidate for candidate in candidates if "diff --git" in candidate]
    if not valid:
        raise ValueError("No valid unified diff candidates")
    return min(valid, key=lambda candidate: sum(1 for line in candidate.splitlines() if line.startswith(("+", "-"))))
