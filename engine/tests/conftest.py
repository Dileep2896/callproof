import pytest

from callproof.models import Call, Record, Turn
from callproof.source import JsonSource


@pytest.fixture(scope="session")
def src() -> JsonSource:
    return JsonSource()


def make_call(turns, workflow="quote_bundle", line="pc", intake=None, record=None) -> Call:
    return Call(
        id="T-1", scenario="T", version="vt", workflow=workflow, line=line, title="t", caller="c", duration=99,
        turns=[Turn(**t) for t in turns], intake=intake or {}, record=record or Record(source="rated quote"),
    )


OPEN = {"speaker": "agent", "t": 0.5, "text": "Hi, this is the virtual assistant, and this call is recorded."}
