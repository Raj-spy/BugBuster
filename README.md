# BugBuster 🚀

> **"Hum fix suggest nahi karte, fix prove karte hain."** (We don't just guess code fixes—we empirically prove them.)

BugBuster is an autonomous **Test-Driven Development (TDD) Vulnerability Remediation Pipeline** built to eliminate the risk of brittle, hallucinated AI patches. Running natively inside your CI/CD workflow, BugBuster bridges static analysis and functional verification: it intercepts flaws, auto-generates a failing unit test to verify the bug, writes the smallest valid source code patch, and enforces a strict multi-gate criteria check before it ever touches a Pull Request.

---

## ⚡ Core Pipeline Architecture

BugBuster operates on a resilient 7-stage engineering loop designed to operate cleanly within isolated GitHub Action runners:

1.  **Ingest (`engine/ingest.py`):** Loads target application scripts, environment constraints, and file structures into memory buffers.
2.  **Detect (`engine/detect.py`):** Combines deterministic scanners (**Bandit** for injection paths, **Gitleaks** for secret protection) with advanced LLM heuristics to catch logical race conditions.
3.  **TestGen (`engine/testgen.py`):** Generates a precise, standalone `pytest` reproduction file targeting the unique failure surface.
4.  **PatchGen (`engine/patchgen.py`):** Leverages token-optimized instructions via **Groq (`qwen/qwen3.8-27b`)** to generate structural code patches.
5.  **Verify (`engine/verify.py`):** Enforces a strict 4-way proof gate logic and processes runtime traces for automated healing loops.
6.  **Git Ops (`engine/git_ops.py`):** Commits approved structural diff fixes cleanly into an isolated repository branch.
7.  **Report (`engine/report.py`):** Generates exhaustive `bugbuster-report.json` and human-readable `.md` evaluation matrices.

---

## 🚪 The 4-Way Proof Gate Matrix

BugBuster never creates a patch merely because an AI model proposed text. Candidate code changes must pass through four distinct runtime evaluation gates:

*   🔴 **1. The Red Gate:** The generated reproducer test is executed 3 consecutive times on the *original* unpatched codebase—it **must fail 100% of the time** to rule out execution flakiness and prove the bug genuinely exists.
*   🟢 **2. The Green Gate:** Once the patch is applied locally, the reproducer test is rerun and **must return a clear passing check**.
*   🟢 **3. The Regression Gate:** BugBuster triggers the entire pre-existing repository test suite to guarantee that the applied code fix introduces zero collateral damage or structural regressions.
*   🔴 **4. The Mutation Gate:** The validation engine intentionally mutates or inverts the patch logic—the reproducer test **must instantly fail again**, proving that the generated test suite is robust, reactive, and not a false-positive tautology.

---

## 🔄 Self-Healing LLM Correction Loop

If a code patch fails any of the 4 validation criteria gates, BugBuster isolates the target execution stack trace and errors. It automatically channels the raw debugger logs straight back into the LLM context pool, triggering up to **3 sequential, automated self-correction attempts** to resolve syntax issues or missing dependencies before gracefully aborting.

---

## 🏆 Key Competitive Advantage

| Feature / Capability | Traditional AI Fixers | BugBuster |
| :--- | :--- | :--- |
| **Fix Quality Assurance** | Speculative suggestions | Empirically proven fixes |
| **Regression Prevention** | High risk of introducing breaking bugs | Enforces a full repository test run prior to branching |
| **Testing Lifecycle** | Provides zero verification modules | Compiles reusable regression tests for your repository |
| **Developer Review Burden** | Hours of manual replication and testing | 1-Click confident merge backed by a 4-Way Proof Gate |

---

## 🚀 Local Quick Start & Command Structure

### 1. Prerequisites & Environment Setup
Clone the workspace and complete your local package orchestration mapping inside your virtual environment (`.venv`):
```bash
pip install -e .
cp .env.example .env
```
Open your newly created `.env` file and enter your operational credentials:
```env
GROQ_API_KEY="gsk_your_secret_production_key_here"
GITHUB_TOKEN="ghp_your_personal_access_token_here"
```

### 2. Executing BugBuster Locally
To trigger the automated pipeline and ingest a specific targeted script file, use the main file options flag directly on the CLI tool wrapper:
```bash
bugbuster --file demo_app/main.py
```

### 3. Reviewing Local Artifact Reports
Once the execution loop finalizes, check your repository root for comprehensive tracking matrices:
*   `bugbuster-report.json`: Formatted data profiles designed for programmatic SIEM processing.
*   `bugbuster-report.md`: Markdown tables highlighting exact rule matches, test assertions, and structural fixes.

---

## ⚙️ Zero-Friction CI/CD Automation

Integrate BugBuster effortlessly directly into your developer workflows by dropping this automated layout block inside your workflow directories:

```yaml
# .github/workflows/bugbuster.yml
name: BugBuster Autonomous Triage Pipeline
on: [push, pull_request]

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Execute BugBuster Pipeline
        uses: raj-spy/bugbuster-action@v1
        env:
          GROQ_API_KEY: \${{ secrets.GROQ_API_KEY }}
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
```

---

## 👥 Human-In-The-Loop Control
BugBuster isolates bugs, generates regression test frameworks, and manages all PR overhead automatically. However, code integration stays safe—**final merge approvals and repo modifications always remain completely controlled by the human developer.**
