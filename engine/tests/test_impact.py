import json

from callproof.cli import main, snapshot
from callproof.impact import measure_impact


def test_impact_numbers(src):
    m = measure_impact(src)
    assert (m["calls"], m["failing_calls"], m["findings"], m["critical"], m["high"]) == (24, 8, 10, 5, 5)
    assert m["grounding_findings"] == 2
    assert m["spoken_figures_checked"] > 40
    assert m["gate"]["v15"]["verdict"] == "BLOCK" and m["gate"]["v15.1"]["verdict"] == "PASS"
    assert [r["label"] for r in m["rows"]][2] == "Critical regressions shipped by prompt v15"
    assert m["rows"][2]["before"] == "1 (no gate)"


def test_impact_is_deterministic(src):
    assert measure_impact(src) == measure_impact(src)


def test_cli_gate_exit_codes(capsys):
    assert main(["gate", "--candidate", "v15"]) == 1
    assert "BLOCK" in capsys.readouterr().out
    assert main(["gate", "--candidate", "v15.1"]) == 0


def test_cli_audit(capsys):
    assert main(["audit"]) == 0
    assert "8 of 24 calls failed" in capsys.readouterr().out


def test_snapshot_round_trip(src, tmp_path):
    out = tmp_path / "snap.json"
    assert main(["snapshot", str(out)]) == 0
    snap = json.loads(out.read_text())
    assert set(snap) == {"health", "rules", "lists", "calls", "suite", "gates", "impact"}
    assert len(snap["calls"]) == 72 and set(snap["gates"]) == {"v14..v15", "v14..v15.1"}
    assert snapshot(src)["impact"] == snap["impact"]
