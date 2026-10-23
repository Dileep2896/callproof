"""Data shapes for calls, audits and gate results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Speaker = Literal["agent", "caller", "tool"]
Severity = Literal["critical", "high"]
Workflow = Literal["quote_bundle", "vehicle_add", "mortgagee_change", "medicare_fronter"]
Period = Literal["year", "month", "six_months"]


class Turn(BaseModel):
    speaker: Speaker
    t: float = Field(ge=0, description="seconds from call start")
    text: str = ""
    tool: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)


class Amount(BaseModel):
    label: str
    value: float
    period: Period | None = None


class Record(BaseModel):
    """The system-of-record payload the call must agree with (rated quote or policy)."""

    source: str
    carriers: list[str] = Field(default_factory=list)
    prior_carrier: str | None = None
    amounts: list[Amount] = Field(default_factory=list)


class Call(BaseModel):
    id: str
    scenario: str
    version: str
    workflow: Workflow
    line: Literal["pc", "medicare"]
    title: str
    caller: str
    duration: float
    turns: list[Turn]
    intake: dict[str, Any]
    record: Record


class Finding(BaseModel):
    rule: str
    severity: Severity
    message: str
    turn: int | None = None
    start: int = 0
    end: int = 0
    t: float | None = None


class Audit(BaseModel):
    call_id: str
    scenario: str
    version: str
    workflow: Workflow
    passed: bool
    score: int
    findings: list[Finding]


class Case(BaseModel):
    case_id: str
    kind: Literal["regression", "guard"]
    workflow: Workflow
    mined_from: str
    baseline_rules: list[str]


class GateRow(BaseModel):
    case_id: str
    workflow: Workflow
    kind: Literal["regression", "guard"]
    status: Literal["ok", "fixed", "regressed", "still_failing"]
    baseline_rules: list[str]
    candidate_rules: list[str]
    new_critical: list[str]


class GateResult(BaseModel):
    baseline: str
    candidate: str
    verdict: Literal["PASS", "BLOCK"]
    reasons: list[str]
    counts: dict[str, int]
    rows: list[GateRow]
