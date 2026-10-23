"""Hard-case mining and the regression gate."""

from __future__ import annotations

from .audit import audit_call, failing_rules
from .models import Audit, Case, GateResult, GateRow
from .source import CallSource


def audit_version(source: CallSource, version: str) -> dict[str, Audit]:
    return {c.scenario: audit_call(c) for c in source.list_calls(version)}


def mine_cases(baseline: dict[str, Audit]) -> list[Case]:
    """Every failing baseline call becomes a regression case; passing calls are kept as guard cases."""
    cases = [
        Case(case_id=s, kind="regression" if not a.passed else "guard", workflow=a.workflow,
             mined_from=a.call_id, baseline_rules=failing_rules(a))
        for s, a in baseline.items()
    ]
    cases.sort(key=lambda c: (c.kind != "regression", c.case_id))
    return cases


def run_gate(source: CallSource, baseline: str, candidate: str) -> GateResult:
    versions = source.versions()
    for v in (baseline, candidate):
        if v not in versions:
            raise KeyError(v)
    base = audit_version(source, baseline)
    cand = audit_version(source, candidate)
    rows: list[GateRow] = []
    for case in mine_cases(base):
        c = cand.get(case.case_id)
        cand_rules = failing_rules(c) if c else ["missing_replay"]
        b_pass, c_pass = not case.baseline_rules, not cand_rules
        status = ("ok" if b_pass and c_pass else "fixed" if c_pass else
                  "regressed" if b_pass else "still_failing")
        new_critical = sorted({
            f.rule for f in (c.findings if c else []) if f.severity == "critical" and f.rule not in case.baseline_rules
        })
        rows.append(GateRow(case_id=case.case_id, workflow=case.workflow, kind=case.kind, status=status,
                            baseline_rules=case.baseline_rules, candidate_rules=cand_rules,
                            new_critical=new_critical))
    counts = {s: sum(r.status == s for r in rows) for s in ("ok", "fixed", "regressed", "still_failing")}
    counts["cases"] = len(rows)
    counts["candidate_passing"] = counts["ok"] + counts["fixed"]
    reasons = []
    for r in rows:
        if r.status == "regressed":
            reasons.append(f"{r.case_id} passed on {baseline} and fails on {candidate} ({', '.join(r.candidate_rules)})")
        elif r.new_critical:
            reasons.append(f"{r.case_id} has a new critical finding on {candidate} ({', '.join(r.new_critical)})")
    return GateResult(baseline=baseline, candidate=candidate, verdict="BLOCK" if reasons else "PASS",
                      reasons=reasons, counts=counts, rows=rows)
