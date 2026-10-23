from fastapi.testclient import TestClient

from callproof.api import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health").json()
    assert r["ok"] and r["versions"] == ["v14", "v15", "v15.1"] and r["baseline"] == "v14"


def test_calls_list_and_detail():
    rows = client.get("/api/calls", params={"version": "v14"}).json()
    assert len(rows) == 24 and sum(not r["passed"] for r in rows) == 8
    d = client.get("/api/calls/Q03-v14").json()
    assert d["call"]["scenario"] == "Q03" and d["audit"]["findings"][0]["rule"] == "grounding"


def test_404s():
    assert client.get("/api/calls/NOPE").status_code == 404
    assert client.get("/api/calls", params={"version": "v99"}).status_code == 404
    assert client.get("/api/gate", params={"candidate": "v99"}).status_code == 404


def test_gate_suite_rules_impact():
    assert client.get("/api/gate", params={"candidate": "v15"}).json()["verdict"] == "BLOCK"
    assert client.get("/api/gate", params={"candidate": "v15.1"}).json()["verdict"] == "PASS"
    assert len(client.get("/api/suite").json()) == 24
    assert len(client.get("/api/rules").json()) == 7
    assert client.get("/api/impact").json()["failing_calls"] == 8
