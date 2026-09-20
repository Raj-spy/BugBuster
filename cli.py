"""BugBuster CLI.

Usage:
    bugbuster run --pr <URL>
    bugbuster run --repo <URL>
    bugbuster run --diff <path/to/file.patch>
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer

from engine.detect import run_all
from engine.git_ops import safe_handle_proven_fix
from engine.ingest import ingest_from_diff, ingest_from_pr, ingest_from_repo
from engine.patchgen import choose_smallest_diff, generate_patch_candidates
from engine.report import build_report, explain_finding, to_markdown
from engine.testgen import generate_test, run_red_check
from engine.verify import run_regression_suite, verify_pipeline_with_retry

app = typer.Typer(help="BugBuster — hum fix suggest nahi karte, fix prove karte hain.")


@app.command()
def run(
    pr: str = typer.Option(None, help="GitHub PR URL"),
    repo: str = typer.Option(None, help="Repo URL (latest changes)"),
    diff: str = typer.Option(None, help="Path to a git diff/patch file"),
    target: str = typer.Option(".", help="Repository directory to scan"),
    output: str = typer.Option("bugbuster-report.md", help="Markdown report path"),
    prove: bool = typer.Option(True, help="Attempt full proof pipeline (Red -> Patch -> Green -> PR)"),
):
    if not any([pr, repo, diff]):
        typer.echo("Provide one of --pr, --repo, or --diff")
        raise typer.Exit(code=1)

    typer.echo("[1/6] Ingesting change...")
    change = ingest_from_pr(pr) if pr else ingest_from_repo(repo) if repo else ingest_from_diff(diff)

    typer.echo("[2/6] Running Bandit, gitleaks, and logic checks...")
    findings = run_all(target, change.diff)
    serialized = [finding.model_dump(mode="json") for finding in findings]
    typer.echo(f"      Detected {len(findings)} finding(s).")

    if not findings:
        typer.echo("[3/6] No security or logic bugs detected. Repository is clean!")
        regression = run_regression_suite()
        report = build_report([], {"status": "none"}, {"red": True, "green": True, "regression": regression, "mutation": True})
        Path(output).write_text(to_markdown(report), encoding="utf-8")
        typer.echo(f"[6/6] Clean report written to {output}")
        return

    # Prioritize findings: changed files > application code > high/medium severity > actionable rules
    def _finding_score(f):
        score = 0
        path = str(f.get("path") or "")
        if change.changed_files and any(cf in path or path in cf for cf in change.changed_files):
            score += 100
        if "demo_app" in path or "app" in path:
            score += 50
        if "tests" in path or "cli.py" in path:
            score -= 50
        sev = str(f.get("severity") or "").lower()
        if sev in ("critical", "high"):
            score += 30
        elif sev == "medium":
            score += 20
        rule = str(f.get("rule_id") or "")
        if rule in ("generic-api-key", "read-write-race", "B608"):
            score += 40
        return score

    sorted_findings = sorted(serialized, key=_finding_score, reverse=True)
    primary_finding = sorted_findings[0]
    typer.echo(f"[3/6] Selected top finding to prove & fix: [{primary_finding.get('rule_id')}] in {primary_finding.get('path')}...")
    explanation = explain_finding(primary_finding)

    test_result = {"status": "skipped"}
    verification_dict = {"red": False, "green": False, "regression": False, "mutation": False}
    final_diff = None

    if prove:
        target_path = Path(primary_finding.get("path") or "demo_app/main.py")
        original_code = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

        # Step 4: Reproducer Test (Red Check)
        typer.echo("[4/6] Generating reproducer test (Red check)...")
        test_code = generate_test(primary_finding, original_code)
        red_passed = run_red_check(test_code, repeat=3)
        test_result = {"code": test_code, "red_passed": red_passed}

        if red_passed:
            typer.echo("      [RED CONFIRMED] Test fails reliably (3x) on buggy code.")
            # Step 5: Patch Generation
            typer.echo("[5/6] Generating patch candidates...")
            candidates = generate_patch_candidates(primary_finding, test_code, original_code, str(target_path))
            if candidates:
                chosen_code, chosen_diff = choose_smallest_diff(candidates)
                typer.echo(f"      Selected minimal patch ({len(chosen_diff.splitlines())} diff lines).")

                # Step 6: 4-Way Verification Gate
                typer.echo("[6/6] Verifying fix via 4-Way Gate (Green, Regression, Mutation)...")
                verification, _, final_diff = verify_pipeline_with_retry(
                    primary_finding, test_code, target_path, chosen_code, chosen_diff
                )
                verification_dict = verification.model_dump(mode="json")

                if verification.green and verification.regression and verification.mutation:
                    typer.echo("      [ALL 4 GATES PASSED] Fix is empirically verified.")
                    # Step 7: Git / PR Automation
                    git_res = safe_handle_proven_fix(
                        branch_name=f"bugbuster/fix-{primary_finding.get('rule_id', 'bug')}",
                        modified_files=[str(target_path)],
                        title=primary_finding.get("message", "Security vulnerability fix"),
                        report_markdown=f"Verified fix for {primary_finding.get('rule_id')}",
                    )
                    if git_res.get("pr_url"):
                        typer.echo(f"      [PR OPENED] {git_res['pr_url']}")
                    else:
                        typer.echo(f"      [BRANCH COMMITTED] {git_res['branch']}")
                else:
                    typer.echo("      [UNVERIFIED] Fix could not be 100% verified across all proof gates.")
            else:
                typer.echo("      [ERROR] No valid patch candidate could be generated.")
        else:
            typer.echo("      [WARN] Reproducer test did not fail consistently (Red check failed). Fix generation halted.")
            verification_dict = {"red": False, "green": False, "regression": run_regression_suite(), "mutation": False}
    else:
        typer.echo("[4/6] Fix proving was disabled via --no-prove.")
        verification_dict = {"red": False, "green": False, "regression": run_regression_suite(), "mutation": False}

    report = build_report(
        serialized,
        test_result,
        verification_dict,
        patch=final_diff,
        explanation=explanation,
    )
    report_path = Path(output)
    report_path.write_text(to_markdown(report), encoding="utf-8")
    report_path.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    typer.echo(f"Proof report written to {report_path}")


@app.command()
def version():
    """Print BugBuster version."""
    typer.echo("BugBuster v0.1.0")


if __name__ == "__main__":
    app()
