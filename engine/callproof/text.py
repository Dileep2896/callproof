"""Text helpers: spoken money extraction with billing period, phrase search, digit normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MONEY = re.compile(
    r"\$\s?(?P<a>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<c>\d{2}))?"
    r"|(?P<b>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<d>\d{2}))?\s+dollars\b",
    re.IGNORECASE,
)

_PERIODS: list[tuple[str, re.Pattern[str]]] = [
    ("six_months", re.compile(r"^\W{0,3}(?:for|per|every)?\s*(?:six|6)[- ]months?\b|^\W{0,3}per term\b", re.IGNORECASE)),
    ("month", re.compile(r"^\W{0,3}(?:a|per|each|every)\s+month\b|^\W{0,3}monthly\b|^\s*/\s*mo\b", re.IGNORECASE)),
    ("year", re.compile(r"^\W{0,3}(?:a|per|each|every)\s+year\b|^\W{0,3}annual(?:ly)?\b|^\s*/\s*yr\b", re.IGNORECASE)),
]


@dataclass(frozen=True)
class Money:
    value: float
    start: int
    end: int
    period: str | None


def extract_money(text: str) -> list[Money]:
    """Find dollar figures in spoken text and the billing period said right after them, if any."""
    out: list[Money] = []
    for m in _MONEY.finditer(text):
        whole = m.group("a") or m.group("b")
        cents = m.group("c") or m.group("d")
        value = float(whole.replace(",", "")) + (int(cents) / 100 if cents else 0.0)
        tail = text[m.end() : m.end() + 24]
        period = next((name for name, rx in _PERIODS if rx.search(tail)), None)
        end = m.end()
        out.append(Money(value=value, start=m.start(), end=end, period=period))
    return out


def find_phrase(text: str, phrases: list[str]) -> tuple[int, int] | None:
    """First case-insensitive occurrence of any phrase, as a (start, end) char span."""
    low = text.lower()
    best: tuple[int, int] | None = None
    for p in phrases:
        i = low.find(p.lower())
        if i >= 0 and (best is None or i < best[0]):
            best = (i, i + len(p))
    return best


def has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) is not None


_SPOKEN_DIGITS = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


def normalize_ident(text: str) -> str:
    """Uppercase alphanumerics only, with spoken digits ('six two nine') folded to digits."""
    words = re.split(r"(\W+)", text)
    folded = "".join(_SPOKEN_DIGITS.get(w.lower(), w) for w in words)
    return re.sub(r"[^A-Za-z0-9]", "", folded).upper()
