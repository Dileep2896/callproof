from callproof.audit import audit_call, failing_rules
from callproof.gate import audit_version
from callproof.rules import RULE_INFO, RULES

EXPECTED_V14 = {
    "Q03": ["grounding"], "Q05": ["grounding", "scope_guard"], "V02": ["intake_complete"],
    "V04": ["intake_faithful"], "M03": ["verify_before_change"], "M05": ["ai_disclosure"],
    "F02": ["tpmo_disclaimer"], "F04": ["scope_guard", "tpmo_disclaimer"],
}


def test_seed_shape(src):
    assert src.versions() == ["v14", "v15", "v15.1"]
    for v in src.versions():
        calls = src.list_calls(v)
        assert len(calls) == 24
        assert {c.workflow for c in calls} == {"quote_bundle", "vehicle_add", "mortgagee_change", "medicare_fronter"}


def test_v14_flags_exactly_the_seeded_defects(src):
    audits = audit_version(src, "v14")
    failing = {s: failing_rules(a) for s, a in audits.items() if not a.passed}
    assert failing == EXPECTED_V14


def test_every_rule_fires_on_v14(src):
    fired = {f.rule for a in audit_version(src, "v14").values() for f in a.findings}
    assert fired == set(RULES) == {r["id"] for r in RULE_INFO}


def test_scores(src):
    audits = audit_version(src, "v14")
    assert audits["Q01"].score == 100
    assert audits["Q05"].score == 40  # critical 40 + high 20
    assert audits["F04"].score == 40
    assert audits["V02"].score == 80


def test_findings_sorted_by_time_and_spans_valid(src):
    for c in src.list_calls("v14"):
        a = audit_call(c)
        ts = [f.t if f.t is not None else 1e9 for f in a.findings]
        assert ts == sorted(ts)
        for f in a.findings:
            if f.turn is not None and f.end > f.start:
                assert 0 <= f.start < f.end <= len(c.turns[f.turn].text)


def test_f02_disclaimer_is_actually_late(src):
    [f] = audit_call(src.get_call("F02-v14")).findings
    assert f.t > 60


def test_v151_is_clean(src):
    assert all(a.passed for a in audit_version(src, "v15.1").values())
