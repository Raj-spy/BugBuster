from pathlib import Path

from engine.detect import detect_logic_bugs, run_gitleaks
from engine.ingest import ingest_from_diff
from engine.report import build_report, to_markdown
from engine.verify import run_green_check, run_mutation_check


def test_ingest_extracts_changed_file(tmp_path: Path):
    patch = tmp_path / "change.diff"
    patch.write_text("diff --git a/a.py b/a.py\n+++ b/a.py\n")
    assert ingest_from_diff(str(patch)).changed_files == ["a.py"]


def test_logic_heuristic_detects_transfer_pattern():
    findings = detect_logic_bugs("SELECT balance\nUPDATE accounts SET balance")
    assert findings[0].rule_id == "read-write-race"


def test_demo_key_is_reported_without_exposing_a_real_credential(tmp_path: Path):
    (tmp_path / "app.py").write_text('API_KEY = "sk-live-REPLACE_WITH_FAKE_DEMO_KEY_1234567890"')
    assert run_gitleaks(str(tmp_path))[0].rule_id == "generic-api-key"


def test_report_says_a_fix_is_not_proven_without_every_check():
    report = build_report([], {}, {"red": True, "green": True, "regression": True, "mutation": False})
    assert report["proven"] is False
    assert "Mutation check: ❌" in to_markdown(report)


def test_green_and_mutation_helpers():
    test = "from subject import fixed\n\ndef test_fixed():\n    assert fixed()\n"
    assert run_green_check(test, "def fixed():\n    return True\n")
    assert run_mutation_check(test, "def fixed():\n    return True\n")


def test_smallest_diff_selection():
    from engine.patchgen import choose_smallest_diff
    cand1 = ("code1", "--- a\n+++ b\n+1\n+2\n+3\n-4\n-5\n")
    cand2 = ("code2", "--- a\n+++ b\n+1\n-2\n")
    chosen_code, chosen_diff = choose_smallest_diff([cand1, cand2])
    assert chosen_code == "code2"


def test_reproducer_generation_and_red_check():
    from engine.testgen import generate_test, run_red_check
    finding = {"rule_id": "generic-api-key", "path": "demo_app/main.py", "message": "Secret leak"}
    test_code = generate_test(finding)
    assert "test_" in test_code
    # Run red check against old unpatched demo_app - API_KEY is hardcoded so it must fail
    red = run_red_check(test_code, repeat=3)
    assert red is True
