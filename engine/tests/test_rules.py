from conftest import OPEN, make_call

from callproof.models import Amount, Record
from callproof.rules import (
    ai_disclosure,
    grounding,
    intake_complete,
    intake_faithful,
    scope_guard,
    tpmo_disclaimer,
    verify_before_change,
)

QUOTE = Record(source="rated quote", carriers=["Cedar Ridge"], prior_carrier="Lakemont", amounts=[
    Amount(label="annual premium", value=1416, period="year"),
    Amount(label="monthly premium", value=118, period="month"),
])
TPMO = "We do not offer every plan available. Call 1-800-MEDICARE for all options."


def test_ai_disclosure_passes_when_opening_has_both():
    assert ai_disclosure(make_call([OPEN])) == []


def test_ai_disclosure_fails_without_recorded_line():
    [f] = ai_disclosure(make_call([{"speaker": "agent", "t": 0.5, "text": "Hi, I'm a virtual assistant."}]))
    assert f.rule == "ai_disclosure" and f.turn == 0


def test_ai_disclosure_late_counts_as_missing():
    late = {"speaker": "agent", "t": 20, "text": "I'm a virtual assistant on a recorded line."}
    turns = [{"speaker": "agent", "t": 0.5, "text": "Hello!"}, late]
    assert len(ai_disclosure(make_call(turns))) == 1


def test_tpmo_only_on_medicare_lines():
    assert tpmo_disclaimer(make_call([OPEN])) == []


def test_tpmo_missing():
    [f] = tpmo_disclaimer(make_call([OPEN], workflow="medicare_fronter", line="medicare"))
    assert f.severity == "critical" and "never" in f.message


def test_tpmo_late_and_on_time():
    late = make_call([OPEN, {"speaker": "agent", "t": 61, "text": TPMO}], line="medicare")
    ok = make_call([OPEN, {"speaker": "agent", "t": 30, "text": TPMO}], line="medicare")
    [f] = tpmo_disclaimer(late)
    assert "61 s" in f.message and f.end > f.start
    assert tpmo_disclaimer(ok) == []


def test_tpmo_needs_both_parts():
    half = make_call([OPEN, {"speaker": "agent", "t": 10, "text": "We do not offer every plan."}], line="medicare")
    assert len(tpmo_disclaimer(half)) == 1


def test_scope_guard_advice_vs_binding():
    advice = {"speaker": "agent", "t": 5, "text": "I'd recommend the cheaper one."}
    bind = {"speaker": "agent", "t": 5, "text": "Great news, you're covered today."}
    assert scope_guard(make_call([advice], line="medicare"))[0].message.count("plan advice") == 1
    assert scope_guard(make_call([advice])) == []
    [f] = scope_guard(make_call([bind]))
    assert "binding" in f.message


def test_scope_guard_ignores_caller():
    assert scope_guard(make_call([{"speaker": "caller", "t": 5, "text": "you're covered?"}])) == []


def test_grounding_passes_matching_figures():
    t = {"speaker": "agent", "t": 5, "text": "Cedar Ridge is $1,416 a year, or $118 a month."}
    assert grounding(make_call([t], record=QUOTE)) == []


def test_grounding_flags_hallucinated_figure_with_closest_hint():
    t = {"speaker": "agent", "t": 5, "text": "That comes to $1,461 a year."}
    [f] = grounding(make_call([t], record=QUOTE))
    assert f.severity == "critical" and "$1,416" in f.message and t["text"][f.start:f.end] == "$1,461"


def test_grounding_flags_wrong_billing_period():
    t = {"speaker": "agent", "t": 5, "text": "Only $118 a year."}
    [f] = grounding(make_call([t], record=QUOTE))
    assert "wrong billing period" in f.message


def test_grounding_one_dollar_tolerance():
    t = {"speaker": "agent", "t": 5, "text": "$1,417 a year"}
    assert grounding(make_call([t], record=QUOTE)) == []


def test_grounding_flags_unquoted_carrier_but_allows_prior():
    t = {"speaker": "agent", "t": 5, "text": "Versus your Lakemont policy, Summit Plains might be cheaper."}
    [f] = grounding(make_call([t], record=QUOTE))
    assert "Summit Plains" in f.message


def test_intake_complete():
    full = {"vin": "X1234", "primary_driver": "a", "lienholder": "b", "lienholder_address": "c"}
    assert intake_complete(make_call([OPEN], workflow="vehicle_add", intake=full)) == []
    [f] = intake_complete(make_call([OPEN], workflow="vehicle_add", intake={**full, "lienholder_address": ""}))
    assert "lienholder_address" in f.message


def test_intake_faithful_last4():
    said = {"speaker": "caller", "t": 4, "text": "VIN ending 6 2 8 9"}
    good = make_call([said], workflow="vehicle_add", intake={"vin": "3FTTW8F9XRR106289"})
    bad = make_call([said], workflow="vehicle_add", intake={"vin": "3FTTW8F9XRR106298"})
    assert intake_faithful(good) == []
    assert "6298" in intake_faithful(bad)[0].message


def test_intake_faithful_only_caller_speech():
    agent_said = {"speaker": "agent", "t": 4, "text": "loan 30-11111"}
    c = make_call([agent_said], workflow="mortgagee_change", intake={"loan_number": "30-11111"})
    assert len(intake_faithful(c)) == 1


def test_verify_before_change():
    v = {"speaker": "tool", "t": 3, "tool": "identity_verified"}
    w = {"speaker": "tool", "t": 9, "tool": "update_mortgagee"}
    assert verify_before_change(make_call([v, w], workflow="mortgagee_change")) == []
    [f] = verify_before_change(make_call([w, v], workflow="mortgagee_change"))
    assert f.severity == "critical" and f.turn == 0


def test_verify_not_applied_to_quotes():
    w = {"speaker": "tool", "t": 9, "tool": "submit_endorsement"}
    assert verify_before_change(make_call([w])) == []
