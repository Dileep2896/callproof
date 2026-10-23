"""Run every rule over a call and score it."""

from __future__ import annotations

from .models import Audit, Call
from .rules import RULES

WEIGHTS = {"critical": 40, "high": 20}


def audit_call(call: Call) -> Audit:
    findings = [f for rule in RULES.values() for f in rule(call)]
    findings.sort(key=lambda f: (f.t if f.t is not None else 1e9, f.rule))
    score = max(0, 100 - sum(WEIGHTS[f.severity] for f in findings))
    return Audit(
        call_id=call.id, scenario=call.scenario, version=call.version, workflow=call.workflow,
        passed=not findings, score=score, findings=findings,
    )


def failing_rules(audit: Audit) -> list[str]:
    return sorted({f.rule for f in audit.findings})
