"""REST API for the console."""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query

from . import ENGINE_VERSION
from .audit import audit_call
from .gate import audit_version, mine_cases, run_gate
from .impact import measure_impact
from .rules import RULE_INFO
from .source import JsonSource

app = FastAPI(title="Callproof", version=ENGINE_VERSION)


@lru_cache(maxsize=1)
def source() -> JsonSource:
    return JsonSource()


def _version(v: str) -> str:
    if v not in source().versions():
        raise HTTPException(404, f"unknown version {v}")
    return v


@app.get("/api/health")
def health() -> dict:
    s = source()
    return {"ok": True, "engine": ENGINE_VERSION, "agency": s.agency, "versions": s.versions(),
            "baseline": s.baseline, "notes": s.notes}


@app.get("/api/rules")
def rules() -> list[dict]:
    return RULE_INFO


@app.get("/api/calls")
def calls(version: str = Query("v14")) -> list[dict]:
    v = _version(version)
    out = []
    for c in source().list_calls(v):
        a = audit_call(c)
        out.append({"id": c.id, "scenario": c.scenario, "version": c.version, "workflow": c.workflow,
                    "title": c.title, "caller": c.caller, "duration": c.duration, "passed": a.passed,
                    "score": a.score, "rules": sorted({f.rule for f in a.findings})})
    return out


@app.get("/api/calls/{call_id}")
def call(call_id: str) -> dict:
    c = source().get_call(call_id)
    if c is None:
        raise HTTPException(404, f"unknown call {call_id}")
    return {"call": c.model_dump(), "audit": audit_call(c).model_dump()}


@app.get("/api/suite")
def suite(baseline: str = Query("v14")) -> list[dict]:
    return [c.model_dump() for c in mine_cases(audit_version(source(), _version(baseline)))]


@app.get("/api/gate")
def gate(baseline: str = Query("v14"), candidate: str = Query("v15")) -> dict:
    return run_gate(source(), _version(baseline), _version(candidate)).model_dump()


@app.get("/api/impact")
def impact() -> dict:
    return measure_impact(source())
