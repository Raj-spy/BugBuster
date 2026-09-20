"""Generate proof report (markdown + JSON) for a bug/fix run."""

from datetime import datetime, timezone


def explain_finding(finding: dict) -> str:
    """Use LLM to explain the finding in simple, actionable terms."""
    from engine.llm import call_llm
    prompt = f"""You are a senior security engineer. Explain this code finding clearly and concisely:
Tool: {finding.get('tool')}
Rule ID: {finding.get('rule_id')}
Severity: {finding.get('severity')}
Message: {finding.get('message')}
File: {finding.get('path')}:{finding.get('line')}
Code: {finding.get('evidence')}

Provide:
1. What the bug is
2. Why it happens
3. Real-world impact / exploit scenario
Keep it under 150 words."""
    try:
        return call_llm(prompt, system="You explain software bugs with maximum clarity.")
    except Exception:
        return finding.get("message", "Security/logic issue detected.")


def build_report(
    bug_report: list[dict],
    test_result: dict,
    verify_result: dict,
    patch: str | None = None,
    explanation: str | None = None,
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings": bug_report,
        "explanation": explanation,
        "test": test_result,
        "patch": patch,
        "verification": verify_result,
        "proven": all(verify_result.get(key, False) for key in ("red", "green", "regression", "mutation")),
    }


def to_markdown(report: dict) -> str:
    proven = report.get("proven", False)
    badge = "🟢 **FIX PROVEN & VERIFIED**" if proven else "🔴 **UNVERIFIED / SCAN REPORT ONLY**"
    lines = [
        "# BugBuster Proof Report",
        "",
        f"> *\"Hum fix suggest nahi karte, fix prove karte hain.\"*",
        "",
        f"**Status**: {badge}",
        "",
        "## Findings",
    ]
    findings = report.get("findings", [])
    if not findings:
        lines.append("No findings were reported.")
    for finding in findings:
        loc = f" (`{finding.get('path')}:{finding.get('line')}`)" if finding.get("path") else ""
        lines.append(f"- **{finding.get('severity', 'MEDIUM').upper()}** `{finding.get('rule_id')}`{loc} — {finding.get('message')}")
        if finding.get("evidence"):
            lines.append(f"  ```python\n  {finding.get('evidence').strip()}\n  ```")

    explanation = report.get("explanation")
    if explanation:
        lines.extend(["", "## Root Cause & Impact", explanation])

    verification = report.get("verification", {})
    lines.extend([
        "",
        "## Proof",
        f"- Red test: {'✅' if verification.get('red') else '❌'}",
        f"- Green test: {'✅' if verification.get('green') else '❌'}",
        f"- Regression suite: {'✅' if verification.get('regression') else '❌'}",
        f"- Mutation check: {'✅' if verification.get('mutation') else '❌'}",
        "",
        "## 4-Way Verification Proof Gate",
        "| Gate | Requirement | Status |",
        "| :--- | :--- | :---: |",
        f"| **1. Red Check** | Reproducer test fails on old code (3x stable) | {'✅ PASS' if verification.get('red') else '❌ FAIL'} |",
        f"| **2. Green Check** | Reproducer test passes on patched code | {'✅ PASS' if verification.get('green') else '❌ FAIL'} |",
        f"| **3. Regression** | Entire existing test suite passes without breaks | {'✅ PASS' if verification.get('regression') else '❌ FAIL'} |",
        f"| **4. Mutation Check** | Inverting patch causes test to fail again | {'✅ PASS' if verification.get('mutation') else '❌ FAIL'} |",
        "",
    ])

    test_code = report.get("test", {}).get("code")
    if test_code:
        lines.extend(["### Generated Reproducer Test (`pytest`)", "```python", test_code.strip(), "```", ""])

    patch_code = report.get("patch")
    if patch_code:
        lines.extend(["### Verified Patch Diff", "```diff", patch_code.strip(), "```", ""])

    if proven:
        lines.append("**Result**: All proof checks passed! Fix is verified and safe for production.")
    else:
        lines.append("**Result**: Fix has NOT passed all 4 gates. No PR will be opened without proof.")

    return "\n".join(lines) + "\n"
