import pytest

from callproof.text import extract_money, find_phrase, has_word, normalize_ident


def test_dollar_with_commas_and_period():
    [m] = extract_money("Northfield came back at $1,416 a year.")
    assert m.value == 1416 and m.period == "year"


def test_monthly_and_no_period():
    ms = extract_money("$1,416, or $118 a month with a $500 deductible")
    assert [(m.value, m.period) for m in ms] == [(1416, None), (118, "month"), (500, None)]


def test_six_month_term():
    [a, b] = extract_money("goes from $742 to $801 per six months")
    assert a.period is None and b.period == "six_months"


def test_cents_and_dollars_word():
    ms = extract_money("that's 89.50 dollars monthly and $12.25")
    assert [(m.value, m.period) for m in ms] == [(89.5, "month"), (12.25, None)]


def test_span_points_at_figure():
    text = "It is $2,184 a year."
    [m] = extract_money(text)
    assert text[m.start:m.end] == "$2,184"


@pytest.mark.parametrize("text", ["100/300/100 limits", "VIN 4471", "March 3rd, 1988"])
def test_non_money_numbers_ignored(text):
    assert extract_money(text) == []


def test_annually_and_slash_yr():
    assert extract_money("$900 annually")[0].period == "year"
    assert extract_money("$75/mo")[0].period == "month"


def test_find_phrase_earliest_case_insensitive():
    assert find_phrase("We DO NOT offer every plan", ["offer every plan", "do not"]) == (3, 9)
    assert find_phrase("nothing here", ["x y"]) is None


def test_has_word_boundaries():
    assert has_word("named Lakemont today", "Lakemont")
    assert not has_word("Lakemonty", "Lakemont")


def test_normalize_ident_spoken_digits():
    assert normalize_ident("VIN ending six two nine eight") == "VINENDING6298"
    assert "3071245" in normalize_ident("loan number is 30-71245.")
