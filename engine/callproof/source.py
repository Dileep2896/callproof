"""CallSource: where calls come from. The bundled JsonSource reads seeded calls; a telephony/STT
feed plus an AMS or rater export would implement the same three methods."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import Call

DATA = Path(__file__).resolve().parent.parent / "data" / "calls.json"


class CallSource(Protocol):
    def versions(self) -> list[str]: ...
    def list_calls(self, version: str) -> list[Call]: ...
    def get_call(self, call_id: str) -> Call | None: ...


class JsonSource:
    def __init__(self, path: Path = DATA) -> None:
        raw = json.loads(path.read_text())
        self.agency: str = raw["agency"]
        self.baseline: str = raw["baseline"]
        self.notes: dict[str, str] = raw.get("notes", {})
        self._calls = [Call.model_validate(c) for c in raw["calls"]]
        self._by_id = {c.id: c for c in self._calls}

    def versions(self) -> list[str]:
        seen: list[str] = []
        for c in self._calls:
            if c.version not in seen:
                seen.append(c.version)
        return seen

    def list_calls(self, version: str) -> list[Call]:
        return [c for c in self._calls if c.version == version]

    def get_call(self, call_id: str) -> Call | None:
        return self._by_id.get(call_id)
