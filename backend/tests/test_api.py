"""API + end-to-end pipeline tests. Network is stubbed with fixtures so the full
11-stage pipeline runs deterministically in seconds. Live-source runs are manual
(see README) and documented as such."""
import time

import pytest
from fastapi.testclient import TestClient

HTML = """
<html><head><title>ACME Corp results</title></head><body><article>
<p>Revenue from operations grew 12 percent to Rs 5,000 crore in FY24.</p>
<p>Net profit fell 8 percent to Rs 400 crore in FY24 on higher provisions.</p>
<p>Operating profit margin compressed to 14.2 percent in FY24.</p>
<p>The board approved a dividend of Rs 12 per share for FY24.</p>
</article></body></html>
"""

SERIES = [
    {"metric": "revenue", "period": "FY2021", "value": 4000.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Sales"},
    {"metric": "revenue", "period": "FY2022", "value": 4400.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Sales"},
    {"metric": "revenue", "period": "FY2023", "value": 4800.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Sales"},
    {"metric": "revenue", "period": "FY2024", "value": 5000.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Sales"},
    {"metric": "pat", "period": "FY2021", "value": 500.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Net Profit"},
    {"metric": "pat", "period": "FY2022", "value": 480.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Net Profit"},
    {"metric": "pat", "period": "FY2023", "value": 440.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Net Profit"},
    {"metric": "pat", "period": "FY2024", "value": 400.0, "units": "INR-cr", "scope": "consolidated", "url": "http://fixture", "table": "Net Profit"},
]


@pytest.fixture()
def client(monkeypatch, tmp_path):
    import os
    dbfile = str(tmp_path / "t.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{dbfile}"

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.db as _db
    import app.models  # noqa: F401 — register tables before create_all

    eng = create_engine(f"sqlite:///{dbfile}", connect_args={"check_same_thread": False})
    NewSession = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    _db.engine = eng
    _db.SessionLocal = NewSession
    _db.Base.metadata.create_all(bind=eng)

    import app.engine.pipeline as P

    def fake_search(query, n=5):
        return [
            {"title": "ACME results FY24", "url": "http://fixture/results", "publisher": "fixture-press"},
            {"title": "ACME annual report", "url": "http://fixture/annual", "publisher": "acme-ir"},
        ]

    def fake_fetch(url):
        return {"ok": True, "url": url, "content_type": "text/html", "content": HTML.encode(), "status": 200}

    def fake_fin(ticker):
        return {"ok": True, "url": "http://fixture", "series": SERIES, "tables_found": 2, "error": ""}

    monkeypatch.setattr(P, "web_search", fake_search)
    monkeypatch.setattr(P, "fetch_url", fake_fetch)
    monkeypatch.setattr(P.SC, "fetch_company_financials", fake_fin)

    from app.main import app
    import app.api.routes as R
    monkeypatch.setattr(R, "SessionLocal", NewSession)
    monkeypatch.setattr(P, "SessionLocal", NewSession)
    # jobs.py imports SessionLocal lazily from app.db at call time — _db patch above covers it.

    with TestClient(app) as c:
        yield c


def _wait_done(c: TestClient, rid: str, timeout: float = 60.0) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = c.get(f"/api/research/{rid}").json()
        if st["status"] in ("completed", "failed", "cancelled"):
            return st
        time.sleep(1.0)
    raise AssertionError("pipeline did not finish in time")


def test_health_and_validation(client):
    assert client.get("/api/health").json()["ok"] is True
    r = client.post("/api/research", json={"company": "x", "track": "A"})
    assert r.status_code == 422  # min_length validation
    r = client.post("/api/research", json={"company": "HDFCBANK", "track": "A"})
    assert r.status_code == 201
    rid = r.json()["id"]
    st = client.get(f"/api/research/{rid}").json()
    assert st["ticker"] == "HDFCBANK" and st["status"] in ("queued", "running", "completed")
    assert client.get("/api/research/nope").status_code == 404
    h = client.get("/api/history").json()
    assert h["total"] >= 1
    _wait_done(client, rid)  # rejoin background job: no detached threads after teardown


def test_end_to_end_pipeline(client):
    rid = client.post("/api/research", json={"company": "ITC", "track": "C", "depth": "quick"}).json()["id"]
    st = _wait_done(client, rid)
    assert st["status"] == "completed", st.get("error")
    assert st["discovery_id"]
    d = client.get(f"/api/discoveries/{st['discovery_id']}").json()
    assert d["headline"] and d["finding"]
    assert d["strength"] in ("Strong", "Moderate", "Weak")
    assert d["counterargument"].get("strongest_alternative")
    assert d["falsification"].get("condition")
    assert d["key_numbers"]  # revenue-up vs pat-down divergence must produce numbers
    ev = client.get(f"/api/discoveries/{st['discovery_id']}/evidence").json()
    assert len(ev["sources"]) >= 2
    assert any(s["evidence"] for s in ev["sources"])  # verbatim passages persisted
    assert any(m["formula"] for m in ev["metrics"])  # provenance on every metric
    exp = client.get(f"/api/discoveries/{st['discovery_id']}/export")
    assert exp.status_code == 200 and "SIGNAL HUNTER X" in exp.text


def test_state_transitions_cancel_retry(client, monkeypatch):
    import app.engine.jobs as J
    monkeypatch.setattr(J, "submit", lambda rid, fn: rid)  # no detached pipeline; state machine only
    rid = client.post("/api/research", json={"company": "ITC", "track": "C", "depth": "quick"}).json()["id"]
    assert client.post(f"/api/research/{rid}/retry").status_code == 409  # still queued/running
    r = client.post(f"/api/research/{rid}/cancel").json()
    assert r["status"] == "cancelled"
    r2 = client.post(f"/api/research/{rid}/retry").json()
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
    assert all(p["scope"] == "consolidated" for p in s)
