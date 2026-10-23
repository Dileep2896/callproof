"""The seven deterministic call rules. Each takes a Call and returns Findings with evidence spans."""

from __future__ import annotations

from collections.abc import Callable

from .models import Call, Finding
from .text import extract_money, find_phrase, has_word, normalize_ident

KNOWN_CARRIERS = [
    "Northfield Mutual", "Cedar Ridge", "Bayline Casualty", "Summit Plains",
    "Granite Shore", "Keystone Harbor", "Lakemont",
]

AI_WORDS = ["virtual assistant", "automated assistant", "ai assistant", "an ai"]
RECORDED_WORDS = ["recorded", "recording"]
DISCLOSURE_DEADLINE_S = 15.0

TPMO_PARTS = [
    ["do not offer every plan", "don't offer every plan"],
    ["1-800-medicare", "medicare.gov"],
]
TPMO_DEADLINE_S = 60.0

ADVICE_PHRASES = ["i'd recommend", "i would recommend", "best plan for you", "you should switch", "you should pick"]
BINDING_PHRASES = ["you're covered", "you are covered", "you're bound", "coverage is in effect", "you're all set with coverage"]

REQUIRED_INTAKE: dict[str, list[str]] = {
    "quote_bundle": ["vehicles", "address", "prior_carrier", "renewal_date"],
    "vehicle_add": ["vin", "primary_driver", "lienholder", "lienholder_address"],
    "mortgagee_change": ["policy_id", "lender", "loan_number"],
    "medicare_fronter": ["zip", "current_plan", "transfer_consent"],
}

# identifier fields whose value must be heard in the caller's own words (last n chars)
IDENT_FIELDS: dict[str, list[tuple[str, int]]] = {
    "vehicle_add": [("vin", 4)],
    "mortgagee_change": [("loan_number", 0)],
    "medicare_fronter": [("zip", 0)],
}

WRITE_TOOLS = {"submit_endorsement", "update_mortgagee"}
SERVICE_WORKFLOWS = {"vehicle_add", "mortgagee_change"}

PERIOD_WORDS = {"year": "a year", "month": "a month", "six_months": "per six months"}


def _agent_turns(call: Call):
    return [(i, t) for i, t in enumerate(call.turns) if t.speaker == "agent"]


def ai_disclosure(call: Call) -> list[Finding]:
    agent = _agent_turns(call)
    if not agent:
        return []
    for i, turn in agent:
        if turn.t > DISCLOSURE_DEADLINE_S:
            break
        ai = find_phrase(turn.text, AI_WORDS)
        rec = find_phrase(turn.text, RECORDED_WORDS)
        if ai and rec:
            return []
    i, first = agent[0]
    return [Finding(
        rule="ai_disclosure", severity="high", turn=i, start=0, end=min(len(first.text), 80), t=first.t,
        message="Opening never says the caller is talking to an AI assistant on a recorded line "
                f"(required in the first {int(DISCLOSURE_DEADLINE_S)} s).",
    )]


def tpmo_disclaimer(call: Call) -> list[Finding]:
    if call.line != "medicare":
        return []
    seen: list[tuple[int, float, tuple[int, int]] | None] = [None] * len(TPMO_PARTS)
    for i, turn in _agent_turns(call):
        for k, options in enumerate(TPMO_PARTS):
            span = find_phrase(turn.text, options)
            if span and seen[k] is None:
                seen[k] = (i, turn.t, span)
    if any(s is None for s in seen):
        i, first = _agent_turns(call)[0]
        return [Finding(
            rule="tpmo_disclaimer", severity="critical", turn=i, start=0, end=0, t=first.t,
            message="The required Medicare third-party marketing disclaimer is never spoken.",
        )]
    latest = max(seen, key=lambda s: s[1])  # type: ignore[arg-type,return-value]
    assert latest is not None
    i, t, span = latest
    if t > TPMO_DEADLINE_S:
        return [Finding(
            rule="tpmo_disclaimer", severity="critical", turn=i, start=span[0], end=span[1], t=t,
            message=f"Medicare disclaimer started at {t:.0f} s; it is required within the first "
                    f"{int(TPMO_DEADLINE_S)} s.",
        )]
    return []


def scope_guard(call: Call) -> list[Finding]:
    phrases = ADVICE_PHRASES if call.line == "medicare" else BINDING_PHRASES
    what = "plan advice (licensed agents only)" if call.line == "medicare" else "binding language (no coverage is bound on a quote call)"
    out = []
    for i, turn in _agent_turns(call):
        span = find_phrase(turn.text, phrases)
        if span:
            out.append(Finding(
                rule="scope_guard", severity="high", turn=i, start=span[0], end=span[1], t=turn.t,
                message=f"Agent used {what}: “{turn.text[span[0]:span[1]]}”.",
            ))
    return out


def grounding(call: Call) -> list[Finding]:
    out = []
    amounts = call.record.amounts
    allowed_carriers = set(call.record.carriers) | ({call.record.prior_carrier} if call.record.prior_carrier else set())
    for i, turn in _agent_turns(call):
        for m in extract_money(turn.text):
            same_value = [a for a in amounts if abs(a.value - m.value) <= 1.0]
            exact = [a for a in same_value if m.period is None or a.period is None or a.period == m.period]
            if exact:
                continue
            if same_value:
                a = same_value[0]
                msg = (f"${m.value:,.0f} {PERIOD_WORDS.get(m.period or '', '')} matches the {a.label} "
                       f"({PERIOD_WORDS.get(a.period or '', 'no period')}), spoken with the wrong billing period.")
            else:
                near = min(amounts, key=lambda a: abs(a.value - m.value)) if amounts else None
                hint = f" Closest value in the {call.record.source} is the {near.label}: ${near.value:,.0f}." if near else ""
                msg = f"${m.value:,.0f} does not appear in the {call.record.source}.{hint}"
            out.append(Finding(rule="grounding", severity="critical", turn=i, start=m.start, end=m.end,
                               t=turn.t, message=msg.replace("  ", " ")))
        for name in KNOWN_CARRIERS:
            if name not in allowed_carriers and has_word(turn.text, name):
                span = find_phrase(turn.text, [name])
                assert span is not None
                out.append(Finding(
                    rule="grounding", severity="critical", turn=i, start=span[0], end=span[1], t=turn.t,
                    message=f"Agent named {name}, which was not one of the carriers in the {call.record.source}.",
                ))
    return out


def intake_complete(call: Call) -> list[Finding]:
    missing = [f for f in REQUIRED_INTAKE[call.workflow] if call.intake.get(f) in (None, "", [], {})]
    if not missing:
        return []
    return [Finding(
        rule="intake_complete", severity="high", turn=None, t=None,
        message=f"Structured intake is missing {', '.join(missing)}; the downstream system will reject it.",
    )]


def intake_faithful(call: Call) -> list[Finding]:
    out = []
    heard = [(i, normalize_ident(t.text)) for i, t in enumerate(call.turns) if t.speaker == "caller"]
    for field, tail in IDENT_FIELDS.get(call.workflow, []):
        value = call.intake.get(field)
        if not value:
            continue
        want = normalize_ident(str(value))
        if tail:
            want = want[-tail:]
        if not any(want in h for _, h in heard):
            out.append(Finding(
                rule="intake_faithful", severity="high", turn=None, t=None,
                message=f"Intake {field} “{value}” was never said by the caller"
                        f"{f' (last {tail}: {want})' if tail else ''}; likely a transcription or entry slip.",
            ))
    return out


def verify_before_change(call: Call) -> list[Finding]:
    if call.workflow not in SERVICE_WORKFLOWS:
        return []
    verified = False
    for i, turn in enumerate(call.turns):
        if turn.speaker != "tool":
            continue
        if turn.tool == "identity_verified":
            verified = True
        elif turn.tool in WRITE_TOOLS and not verified:
            return [Finding(
                rule="verify_before_change", severity="critical", turn=i, t=turn.t,
                message=f"{turn.tool} ran at {turn.t:.0f} s before the caller's identity was verified.",
            )]
    return []


RULES: dict[str, Callable[[Call], list[Finding]]] = {
    "ai_disclosure": ai_disclosure,
    "tpmo_disclaimer": tpmo_disclaimer,
    "scope_guard": scope_guard,
    "grounding": grounding,
    "intake_complete": intake_complete,
    "intake_faithful": intake_faithful,
    "verify_before_change": verify_before_change,
}

RULE_INFO = [
    {"id": "ai_disclosure", "severity": "high", "check": "AI assistant + recorded line said in the opening (by 15 s)"},
    {"id": "tpmo_disclaimer", "severity": "critical", "check": "Medicare marketing disclaimer spoken by 60 s"},
    {"id": "scope_guard", "severity": "high", "check": "No plan advice (Medicare) or binding language (quotes)"},
    {"id": "grounding", "severity": "critical", "check": "Every spoken dollar figure and carrier matches the record"},
    {"id": "intake_complete", "severity": "high", "check": "Required fields for the workflow are captured"},
    {"id": "intake_faithful", "severity": "high", "check": "Identifiers in the intake were said by the caller"},
    {"id": "verify_before_change", "severity": "critical", "check": "Identity verified before any policy write"},
]
