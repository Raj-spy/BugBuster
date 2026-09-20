# 🛡️ Autonomous Code Security & Repair Engine

> **Detect → Reproduce → Patch → Prove → Ship**

An autonomous security and code-repair engine that combines **local static analysis, LLM-assisted reasoning, deterministic test reproduction, multi-stage validation, and automated GitHub PRs** to identify and repair software vulnerabilities and concurrency-related defects.

Unlike conventional AI coding agents that primarily generate patches, this system treats a patch as **untrusted until it is empirically proven correct**.

---

## 🚀 Why This Exists

Modern AI coding agents can generate fixes quickly, but generating a patch is only one part of reliable software engineering.

A generated patch can:

* Fix the reported issue but introduce a regression.
* Pass a weak or incorrectly designed test.
* Modify more code than necessary.
* Produce a flaky reproducer.
* Appear correct without actually addressing the root cause.
* Break existing repository behavior.

This system introduces a **proof-driven repair pipeline** where every generated fix must survive multiple independent validation gates before it can be shipped.

### Core Principle

> **An AI-generated patch is a hypothesis. Tests and validation provide the proof.**

---

# 🧠 Core Capabilities

### 1. Multi-Vector Triage Shield

Combines fast local security scanners with LLM-based reasoning to identify potential issues across multiple vectors.

**Local analysis:**

* [Bandit](https://bandit.readthedocs.io/) — Python security analysis
* [Gitleaks](https://github.com/gitleaks/gitleaks) — secret and credential detection

**AI-assisted analysis:**

* Code-level vulnerability reasoning
* Concurrency and race-condition analysis
* Root-cause identification
* Patch candidate generation

The goal is to combine **deterministic tooling** with **reasoning-based analysis**, rather than relying entirely on an external AI API.

---

## 2. 🔴 Empirical Red-State Proof

The system does not accept a vulnerability merely because an LLM claims that one exists.

It first attempts to construct a **standalone executable reproducer**.

The generated `pytest` reproducer is executed **three consecutive times** against the original code.

```text
Original Code
     │
     ▼
Generate Reproducer
     │
     ▼
Run #1 ── FAIL
     │
     ▼
Run #2 ── FAIL
     │
     ▼
Run #3 ── FAIL
     │
     ▼
Deterministic RED Baseline
```

This establishes empirical evidence that the reported behavior actually exists.

### Why three runs?

Concurrency-related failures can be nondeterministic.

Repeated execution helps distinguish:

```text
Real reproducible failure
        vs.
Flaky / accidental failure
```

---

# 3. 🩹 Minimal Patch Synthesis

Once the failure has been reproduced, the system generates candidate fixes.

Instead of blindly accepting the first generated solution, patches are validated structurally and compared to identify a minimal change.

### Validation

Generated patches are checked using:

* `ast.parse`
* `difflib`
* Patch structure validation
* Syntax validation
* Compilation checks

Conceptually:

```text
Issue
  │
  ▼
Patch Candidates
  │
  ├── Candidate A
  ├── Candidate B
  └── Candidate C
        │
        ▼
Structural Validation
        │
        ▼
Minimal Valid Diff
```

The objective is to reduce unnecessary code changes and keep the resulting patch easy to review.

---

# 4. 🧪 Four-Way Proof Gate

Every patch must pass **four independent validation gates** before it is considered safe to ship.

| Gate                   | Requirement                   | Purpose                              |
| ---------------------- | ----------------------------- | ------------------------------------ |
| 🔴 **Red Gate**        | Test fails on original code   | Proves the issue exists              |
| 🟢 **Green Gate**      | Test passes after patch       | Proves the patch addresses the issue |
| 🔄 **Regression Gate** | Existing tests remain green   | Prevents collateral regressions      |
| 🧬 **Mutation Gate**   | Inverted patch causes failure | Proves the test is meaningful        |

### 🔴 Red Gate

The reproducer **must fail** against the original implementation.

```text
Original Code
     +
Reproducer
     ↓
   FAIL
```

If the test already passes, the system does not have sufficient evidence of a defect.

---

### 🟢 Green Gate

After applying the generated patch:

```text
Patched Code
     +
Reproducer
     ↓
   PASS
```

A patch that does not eliminate the reproduced failure is rejected.

---

### 🔄 Regression Gate

The system then executes the repository's existing test suite.

```text
Existing Test Suite
        │
        ▼
   All Tests PASS
        │
        ▼
No Known Regression
```

This prevents a local fix from breaking unrelated functionality.

---

### 🧬 Mutation Gate

The system additionally validates whether the generated test actually detects the intended behavioral change.

The repair logic is inverted or mutated.

```text
Correct Patch
     ↓
   PASS

Inverted / Mutated Patch
     ↓
   FAIL
```

If the mutated implementation still passes, the test may be too weak or disconnected from the actual fix.

---

# 5. 🔁 Self-Healing Repair Loop

Validation failures are not immediately treated as terminal errors.

The system captures:

* Test failures
* Assertion errors
* Stack traces
* Compilation errors
* Patch application failures
* Regression failures

These diagnostics are fed back into the repair engine.

```text
Generate Patch
      │
      ▼
   Validate
      │
      ├── PASS ──► Continue
      │
      ▼
    ERROR
      │
      ▼
Capture Stack Trace
      │
      ▼
LLM Re-analysis
      │
      ▼
Generate Corrected Patch
      │
      ▼
   Validate Again
```

The repair loop allows up to **3 automated self-correction iterations**.

If the system cannot produce a valid patch within the allowed attempts, the repair is rejected rather than silently modifying the codebase.

---

# 6. 🤖 Autonomous Git PR Pipeline

Once a patch successfully passes all proof gates, the system can complete the software-engineering workflow automatically.

### Pipeline

```text
Detection
   │
   ▼
Reproduction
   │
   ▼
Patch Generation
   │
   ▼
Proof Gates
   │
   ▼
Feature Branch
   │
   ▼
Commit
   │
   ▼
GitHub Pull Request
   │
   ▼
Verification Matrix
```

The generated PR contains the evidence required to review the repair rather than simply presenting an AI-generated diff.

### Verification Matrix

The CI Job Summary can report:

```text
┌──────────────────────────────┬────────┐
│ Validation                   │ Status │
├──────────────────────────────┼────────┤
│ Original reproducer          │  PASS  │
│ Patched reproducer           │  PASS  │
│ Regression suite             │  PASS  │
│ Mutation validation          │  PASS  │
│ AST validation               │  PASS  │
│ Patch integrity              │  PASS  │
└──────────────────────────────┴────────┘
```

---

# 7. ⚡ Low-Latency Inference & Failover

For large patch-generation and reasoning workloads, the system can route inference through **Groq** for low-latency responses.

A fallback model cascade is maintained to reduce dependence on a single inference provider.

```text
             ┌───────────────┐
             │ Primary Model │
             └───────┬───────┘
                     │
                  Failure
                     ▼
             ┌───────────────┐
             │ Fallback Model│
             └───────┬───────┘
                     │
                  Failure
                     ▼
             ┌───────────────┐
             │ Local / Other │
             │    Models     │
             └───────────────┘
```

The architecture is designed so that the **core validation and security pipeline does not depend on a single model provider**.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │     Repository      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Triage Engine     │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
               ┌────────┐     ┌─────────┐     ┌──────────┐
               │ Bandit │     │ Gitleaks│     │   LLM    │
               └────┬───┘     └────┬────┘     └────┬─────┘
                    │              │               │
                    └──────────────┼───────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │   Root Cause Engine │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Reproducer Generator│
                         └──────────┬──────────┘
                                    │
                                    ▼
                              🔴 RED GATE
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Patch Synthesizer  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Structural Validator│
                         └──────────┬──────────┘
                                    │
                                    ▼
                              🟢 GREEN GATE
                                    │
                                    ▼
                           🔄 REGRESSION GATE
                                    │
                                    ▼
                           🧬 MUTATION GATE
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Approved Patch     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Git / GitHub PR   │
                         └─────────────────────┘
```

---

# 🔐 Security Philosophy

The system follows a **defense-in-depth** approach.

Instead of asking:

> "Does the AI think this patch is correct?"

the pipeline asks:

> "Can we demonstrate that the original code fails, the patched code succeeds, existing behavior remains intact, and the test actually detects the intended defect?"

This distinction is fundamental to the architecture.

---

# 🔄 End-to-End Workflow

```text
1. Scan Repository
        ↓
2. Detect Potential Issue
        ↓
3. Analyze Root Cause
        ↓
4. Generate Reproducer
        ↓
5. Establish RED Baseline
        ↓
6. Generate Patch Candidates
        ↓
7. Select Minimal Patch
        ↓
8. Validate Syntax / Structure
        ↓
9. GREEN Validation
        ↓
10. Regression Testing
        ↓
11. Mutation Testing
        ↓
12. Self-Heal if Required
        ↓
13. Create Feature Branch
        ↓
14. Commit Verified Patch
        ↓
15. Open GitHub PR
        ↓
16. Publish Verification Matrix
```

---

# 🧰 Technology Stack

| Layer                 | Technology          |
| --------------------- | ------------------- |
| Language              | Python              |
| Testing               | pytest              |
| Static Security       | Bandit              |
| Secret Detection      | Gitleaks            |
| Code Analysis         | Python AST          |
| Diff Analysis         | difflib             |
| AI Reasoning          | LLM-based inference |
| Low-Latency Inference | Groq                |
| Version Control       | Git                 |
| Collaboration         | GitHub              |
| Automation            | CI/CD               |

---

# 📦 Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install security scanners:

```bash
pip install bandit
```

Install Gitleaks separately according to your operating system.

---

# ⚙️ Configuration

Create the required environment configuration:

```env
MODEL_PROVIDER=groq
MODEL_NAME=<model-name>
GROQ_API_KEY=<your-key>
```

> API credentials should never be committed to the repository.

Add environment files to `.gitignore`:

```gitignore
.env
.env.*
!.env.example
```

---

# ▶️ Usage

Run the security triage:

```bash
python -m engine scan .
```

Generate a reproduction:

```bash
python -m engine reproduce <issue>
```

Generate and validate a repair:

```bash
python -m engine repair <issue>
```

Run the complete proof pipeline:

```bash
python -m engine verify <issue>
```

> Replace the commands above with the project's actual CLI entry points as the implementation evolves.

---

# 🧪 Validation Model

The system considers a repair successful only when the required evidence chain is complete:

```text
Issue Detected
      ↓
Reproducer Fails
      ↓
Patch Applied
      ↓
Reproducer Passes
      ↓
Regression Suite Passes
      ↓
Mutation Test Fails
      ↓
Patch Proven
```

A failure at any critical stage prevents automatic shipment.

---

# 🚧 Design Goals

The project is being designed around several engineering principles:

* **Proof over prediction**
* **Deterministic validation over blind trust**
* **Minimal diffs over unnecessary rewrites**
* **Local tooling over unnecessary API dependency**
* **Defense in depth**
* **Fail closed**
* **Reproducibility**
* **Automated evidence generation**
* **Human-reviewable Git changes**

The objective is not to create another chatbot that writes code.

The objective is to build an **engineering system that can reason about a defect, reproduce it, propose a repair, prove the repair, and produce reviewable software changes.**

---

# 🗺️ Roadmap

### Phase 1 — Core Engine

* [x] Local security scanning
* [x] LLM-assisted issue analysis
* [x] Reproducer generation
* [x] Multi-run RED validation
* [x] Patch generation
* [x] AST validation

### Phase 2 — Proof System

* [x] Red Gate
* [x] Green Gate
* [x] Regression Gate
* [x] Mutation Gate
* [x] Automated repair loop

### Phase 3 — Developer Workflow

* [ ] Git branch automation
* [ ] Automated commits
* [ ] GitHub PR creation
* [ ] CI verification matrix
* [ ] Rich PR reporting

### Phase 4 — Advanced Engineering

* [ ] Concurrency-aware reproduction strategies
* [ ] More language support
* [ ] Local model support
* [ ] Model routing
* [ ] Distributed execution
* [ ] Historical failure learning
* [ ] Repository-specific repair strategies

---

# ⚠️ Current Limitations

Automated code repair is inherently difficult.

The system does **not** assume that an LLM-generated patch is correct simply because:

* The model provides a convincing explanation.
* The code compiles.
* A single test passes.
* The generated diff looks reasonable.

The proof pipeline provides stronger evidence, but no automated validation system can guarantee the absence of every possible defect.

For production repositories, human review remains an important part of the software delivery process.

---

# 🤝 Contributing

Contributions are welcome.

Before submitting a pull request:

1. Create a feature branch.
2. Add or update tests.
3. Ensure the existing test suite passes.
4. Run the security checks.
5. Keep changes focused and minimal.
6. Document architectural changes.

---

# 📄 License

---

## ⭐ Philosophy

**Don't ask an AI whether its code is correct.**

**Make it prove it.**
