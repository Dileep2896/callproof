import pytest

from callproof.gate import audit_version, mine_cases, run_gate


def test_mining_turns_failures_into_regression_cases(src):
    cases = mine_cases(audit_version(src, "v14"))
    reg = [c for c in cases if c.kind == "regression"]
    assert len(reg) == 8 and len(cases) == 24
    assert cases[0].kind == "regression"  # regression cases sort first
    assert all(c.baseline_rules for c in reg)
    assert all(not c.baseline_rules for c in cases if c.kind == "guard")


def test_v15_blocked_by_one_regression(src):
    g = run_gate(src, "v14", "v15")
    assert g.verdict == "BLOCK"
    assert g.counts == {"ok": 15, "fixed": 7, "regressed": 1, "still_failing": 1, "cases": 24,
                        "candidate_passing": 22}
    [row] = [r for r in g.rows if r.status == "regressed"]
    assert row.case_id == "Q01" and row.candidate_rules == ["grounding"] and row.new_critical == ["grounding"]
    assert any("Q01" in r for r in g.reasons)


def test_v151_passes(src):
    g = run_gate(src, "v14", "v15.1")
    assert g.verdict == "PASS" and g.reasons == []
    assert g.counts["fixed"] == 8 and g.counts["candidate_passing"] == 24


def test_self_gate_passes_with_no_changes(src):
    g = run_gate(src, "v14", "v14")
    assert g.verdict == "PASS" and g.counts["ok"] == 16 and g.counts["still_failing"] == 8


def test_new_critical_on_still_failing_case_blocks(src, monkeypatch):
    # F04 still fails on v15 with scope_guard (high) only: not a new critical, so it alone would not block
    g = run_gate(src, "v14", "v15")
    f04 = next(r for r in g.rows if r.case_id == "F04")
    assert f04.status == "still_failing" and f04.new_critical == []


def test_unknown_version(src):
    with pytest.raises(KeyError):
        run_gate(src, "v14", "v99")
