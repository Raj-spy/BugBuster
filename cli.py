"""BugBuster CLI.

Usage:
    bugbuster run --pr <URL>
    bugbuster run --repo <URL>
    bugbuster run --diff <path/to/file.patch>
"""

import json
from pathlib import Path

import typer

from engine.detect import run_all
from engine.ingest import ingest_from_diff, ingest_from_pr, ingest_from_repo
from engine.report import build_report, to_markdown
from engine.verify import run_regression_suite

app = typer.Typer(help="BugBuster — hum fix suggest nahi karte, fix prove karte hain.")


@app.command()
def run(
    pr: str = typer.Option(None, help="GitHub PR URL"),
    repo: str = typer.Option(None, help="Repo URL (latest changes)"),
    diff: str = typer.Option(None, help="Path to a git diff/patch file"),
    target: str = typer.Option(".", help="Repository directory to scan"),
    output: str = typer.Option("bugbuster-report.md", help="Markdown report path"),
):
    if not any([pr, repo, diff]):
        typer.echo("Provide one of --pr, --repo, or --diff")
        raise typer.Exit(code=1)
    typer.echo("[1/6] Ingesting change...")
    change = ingest_from_pr(pr) if pr else ingest_from_repo(repo) if repo else ingest_from_diff(diff)
    typer.echo("[2/6] Running Bandit, gitleaks, and logic checks...")
    findings = run_all(target, change.diff)
    serialized = [finding.model_dump(mode="json") for finding in findings]
    typer.echo(f"[3/6] Explained {len(findings)} finding(s).")
    # Tests and patches are intentionally gated: no LLM-generated change is applied until its
    # red/green/regression/mutation proof exists. This scan report is safe for push workflows.
    typer.echo("[4/6] Test/patch generation is gated pending an approved reproducer.")
    regression = run_regression_suite()
    verification = {"red": False, "green": False, "regression": regression, "mutation": False}
    report = build_report(serialized, {"status": "not-generated"}, verification)
    report_path = Path(output)
    report_path.write_text(to_markdown(report), encoding="utf-8")
    report_path.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    typer.echo(f"[6/6] Report written to {report_path}")
    if findings:
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
