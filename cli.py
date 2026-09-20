"""BugBuster CLI.

Usage:
    bugbuster run --pr <URL>
    bugbuster run --repo <URL>
    bugbuster run --diff <path/to/file.patch>
"""

import typer

app = typer.Typer(help="BugBuster — hum fix suggest nahi karte, fix prove karte hain.")


@app.command()
def run(
    pr: str = typer.Option(None, help="GitHub PR URL"),
    repo: str = typer.Option(None, help="Repo URL (latest changes)"),
    diff: str = typer.Option(None, help="Path to a git diff/patch file"),
):
    if not any([pr, repo, diff]):
        typer.echo("Provide one of --pr, --repo, or --diff")
        raise typer.Exit(code=1)
    typer.echo("[1/6] Input received...")
    # TODO: wire up engine.ingest -> detect -> testgen -> patchgen -> verify -> git_ops -> report


if __name__ == "__main__":
    app()
