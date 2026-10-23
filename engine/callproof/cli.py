"""CLI: audit a version, run the gate (exit 1 on BLOCK, for CI), print impact, write the web snapshot.

  python -m callproof.cli audit [--version v14]
  python -m callproof.cli gate --baseline v14 --candidate v15
  python -m callproof.cli impact
  python -m callproof.cli snapshot ../web/public/snapshot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import audit_call
from .gate import audit_version, mine_cases, run_gate
from .impact import measure_impact
from .rules import RULE_INFO
from .source import JsonSource


def snapshot(source: JsonSource) -> dict:
    versions = source.versions()
    calls = {}
    lists = {}
    for v in versions:
        rows = []
        for c in source.list_calls(v):
            a = audit_call(c)
            calls[c.id] = {"call": c.model_dump(), "audit": a.model_dump()}
            rows.append({"id": c.id, "scenario": c.scenario, "version": c.version, "workflow": c.workflow,
                         "title": c.title, "caller": c.caller, "duration": c.duration, "passed": a.passed,
                         "score": a.score, "rules": sorted({f.rule for f in a.findings})})
        lists[v] = rows
    gates = {f"{source.baseline}..{v}": run_gate(source, source.baseline, v).model_dump()
             for v in versions if v != source.baseline}
    return {
        "health": {"ok": True, "agency": source.agency, "versions": versions, "baseline": source.baseline,
                   "notes": source.notes},
        "rules": RULE_INFO,
        "lists": lists,
        "calls": calls,
        "suite": [c.model_dump() for c in mine_cases(audit_version(source, source.baseline))],
        "gates": gates,
        "impact": measure_impact(source),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="callproof")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit")
    a.add_argument("--version", default="v14")
    g = sub.add_parser("gate")
    g.add_argument("--baseline", default="v14")
    g.add_argument("--candidate", default="v15")
    sub.add_parser("impact")
    s = sub.add_parser("snapshot")
    s.add_argument("out", type=Path)
    args = p.parse_args(argv)
    src = JsonSource()

    if args.cmd == "audit":
        audits = audit_version(src, args.version)
        for sid, au in audits.items():
            mark = "PASS" if au.passed else "FAIL"
            print(f"{sid:5} {mark}  score {au.score:3}  " + "; ".join(f"[{f.rule}] {f.message}" for f in au.findings))
        print(f"{sum(not x.passed for x in audits.values())} of {len(audits)} calls failed")
        return 0
    if args.cmd == "gate":
        res = run_gate(src, args.baseline, args.candidate)
        c = res.counts
        print(f"gate {res.baseline} -> {res.candidate}: {res.verdict}  ok {c['ok']}  fixed {c['fixed']}  "
              f"regressed {c['regressed']}  still failing {c['still_failing']}")
        for r in res.reasons:
            print(f"  - {r}")
        return 1 if res.verdict == "BLOCK" else 0
    if args.cmd == "impact":
        print(json.dumps(measure_impact(src), indent=2))
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot(src)) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
