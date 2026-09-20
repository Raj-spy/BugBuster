# BugBuster

**Hum fix suggest nahi karte, fix prove karte hain.**

Developer pushes -> GitHub Actions runs BugBuster -> bug detected -> failing test
written against old code (red) -> fix generated -> verified (green + regression +
mutation) -> fix PR opened -> human reviews and merges.

## Quick start

```bash
pip install -e .
cp .env.example .env   # fill in your keys
bugbuster run --diff path/to/file.patch
```

The command writes `bugbuster-report.md` and `bugbuster-report.json`. A finding exits
with code 2 so that a CI policy can flag it, while a scanner/tool failure is reported
without silently treating it as a proven fix.

## Proof gate

BugBuster never opens a fix PR merely because an LLM proposed code. A candidate must
have a stable red reproducer (three runs), green result, passing regression suite, and
a mutation check that proves the test detects removal of the fix. The GitHub workflow
currently produces the safe scan report; enable branch/PR credentials only after the
project-specific generated-test reviewer is configured.

## Structure

See \`engine/\` for the pipeline stages (ingest -> detect -> testgen -> patchgen -> verify -> git_ops -> report).

## Limitations

- Python only, for now
- Generated tests cover one reproduction scenario — human review is still required
- Free-tier LLM rate limits apply (hence the failover chain + cache)
- Code is sent to a third-party LLM; self-hosted model support is planned for sensitive repos
