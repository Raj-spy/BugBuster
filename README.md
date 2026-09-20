# BugBuster

**Hum fix suggest nahi karte, fix prove karte hain.**

Developer pushes -> GitHub Actions runs BugBuster -> bug detected -> failing test
written against old code (red) -> fix generated -> verified (green + regression +
mutation) -> fix PR opened -> human reviews and merges.

## Quick start

\`\`\`bash
pip install -e .
cp .env.example .env   # fill in your keys
bugbuster run --diff path/to/file.patch
\`\`\`

## Structure

See \`engine/\` for the pipeline stages (ingest -> detect -> testgen -> patchgen -> verify -> git_ops -> report).

## Limitations

- Python only, for now
- Generated tests cover one reproduction scenario — human review is still required
- Free-tier LLM rate limits apply (hence the failover chain + cache)
- Code is sent to a third-party LLM; self-hosted model support is planned for sensitive repos
