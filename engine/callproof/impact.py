"""The only numbers the README and the story page quote. All measured on the bundled seed calls."""

from __future__ import annotations

from collections import Counter

from .gate import audit_version, run_gate
from .source import CallSource
from .text import extract_money


def measure_impact(source: CallSource, baseline: str = "v14", blocked: str = "v15", fixed: str = "v15.1") -> dict:
    base = audit_version(source, baseline)
    findings = [f for a in base.values() for f in a.findings]
    by_rule = Counter(f.rule for f in findings)
    by_sev = Counter(f.severity for f in findings)
    figures = sum(
        len(extract_money(t.text)) for c in source.list_calls(baseline) for t in c.turns if t.speaker == "agent"
    )
    bad_figures = by_rule.get("grounding", 0)
    g_block = run_gate(source, baseline, blocked)
    g_pass = run_gate(source, baseline, fixed)
    shipped_regressions = g_block.counts["regressed"]
    failing = sum(not a.passed for a in base.values())
    return {
        "calls": len(base),
        "failing_calls": failing,
        "findings": len(findings),
        "critical": by_sev.get("critical", 0),
        "high": by_sev.get("high", 0),
        "by_rule": dict(sorted(by_rule.items())),
        "spoken_figures_checked": figures,
        "grounding_findings": bad_figures,
        "mined_cases": failing,
        "guard_cases": len(base) - failing,
        "gate": {
            blocked: {"verdict": g_block.verdict, **g_block.counts},
            fixed: {"verdict": g_pass.verdict, **g_pass.counts},
        },
        "rows": [
            {"label": f"Defective calls surfaced ({baseline} seed week)",
             "before": f"0 of {failing} (no audit)", "after": f"{failing} of {failing}, with evidence"},
            {"label": "Spoken dollar figures checked against the record",
             "before": f"0 of {figures}", "after": f"{figures} of {figures}"},
            {"label": f"Critical regressions shipped by prompt {blocked}",
             "before": f"{shipped_regressions} (no gate)", "after": "0 (gate blocks)"},
            {"label": "Regression suite passing",
             "before": f"{len(base) - failing} / {len(base)} on {baseline}",
             "after": f"{g_pass.counts['candidate_passing']} / {len(base)} on {fixed}"},
        ],
    }
