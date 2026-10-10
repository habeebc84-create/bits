import json

from fastapi.testclient import TestClient


def _client():
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test_shx.db")
    # isolate test DB
    try:
        os.remove("./test_shx.db")
    except OSError:
        pass
    from app.main import app
    return TestClient(app)


def test_health_and_validation():
    c = _client()
    assert c.get("/api/health").json()["ok"] is True
    r = c.post("/api/research", json={"company": "x", "track": "A"})
    assert r.status_code == 422  # min_length validation
    r = c.post("/api/research", json={"company": "HDFCBANK", "track": "A"})
    assert r.status_code == 201
    rid = r.json()["id"]
    st = c.get(f"/api/research/{rid}").json()
    assert st["ticker"] == "HDFCBANK" and st["status"] in ("queued", "running", "completed")
    assert c.get("/api/research/nope").status_code == 404
    h = c.get("/api/history").json()
    assert h["total"] >= 1


def test_state_transitions_cancel_retry():
    c = _client()
    rid = c.post("/api/research", json={"company": "ITC", "track": "C", "depth": "quick"}).json()["id"]
    # retry while queued/running -> 409
    assert c.post(f"/api/research/{rid}/retry").status_code == 409
    r = c.post(f"/api/research/{rid}/cancel").json()
    assert r["status"] == "cancelled"
    r2 = c.post(f"/api/research/{rid}/retry").json()
    assert r2["status"] == "queued"


def test_screener_parser_fixture():
    from app.services.screener import parse_screener_tables, to_annual_series
    html = """<table><thead><tr><th>Narration</th><th>Mar 2021</th><th>Mar 2022</th><th>Mar 2023</th></tr></thead>
    <tbody><tr><td>Sales</td><td>1,000</td><td>1,100</td><td>1,320</td></tr>
    <tr><td>Net Profit</td><td>100</td><td>110</td><td>99</td></tr></tbody></table>"""
    t = parse_screener_tables(html)
    assert "sales" in t and "net profit" in t
    s = to_annual_series(t, "TEST", "http://x")
    rev = [p for p in s if p["metric"] == "revenue"]
    assert [p["period"] for p in rev] == ["FY2021", "FY2022", "FY2023"]
    # standalone vs consolidated separation: scope tagged
    assert all(p["scope"] == "consolidated" for p in s)
