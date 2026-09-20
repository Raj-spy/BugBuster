"""Generate proof report (markdown + JSON) for a bug/fix run."""

from datetime import datetime, timezone


def build_report(bug_report: dict, test_result: dict, verify_result: dict) -> dict:
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "findings": bug_report,
            "test": test_result, "verification": verify_result,
            "proven": all(verify_result.get(key, False) for key in ("red", "green", "regression", "mutation"))}


def to_markdown(report: dict) -> str:
    lines = ["# BugBuster proof report", "", "## Findings"]
    findings = report.get("findings", [])
    if not findings:
        lines.append("No findings were reported.")
    for finding in findings:
        lines.append(f"- **{finding['severity'].upper()}** `{finding['rule_id']}` — {finding['message']}")
    verification = report.get("verification", {})
    lines.extend(["", "## Proof", f"- Red test: {'✅' if verification.get('red') else '❌'}",
                  f"- Green test: {'✅' if verification.get('green') else '❌'}",
                  f"- Regression suite: {'✅' if verification.get('regression') else '❌'}",
                  f"- Mutation check: {'✅' if verification.get('mutation') else '❌'}",
                  "", "**A fix PR may be opened only when every proof check passes.**"])
    return "\n".join(lines) + "\n"
