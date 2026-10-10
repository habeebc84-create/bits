"""Seed a clearly-labeled demonstration investigation (fixture, not live research).

Usage: python -m app.seed_demo  (run from backend/ with the venv active)
"""
from __future__ import annotations

import json

from .db import SessionLocal, init_db
from .models import Discovery, Investigation


def main() -> str:
    init_db()
    db = SessionLocal()
    try:
        inv = Investigation(company_id="demo", company_name="Demo Company (Illustrative Fixture)",
                            ticker="DEMO", exchange="NSE", track="C", period="FY2022-FY2025",
                            depth="standard", status="completed", stage="report")
        db.add(inv)
        db.commit()
        d = Discovery(
            investigation_id=inv.id,
            headline="DEMO (fictional): PAT outpaced operating cash flow two years running",
            finding=("ILLUSTRATIVE FIXTURE — not live research. Demonstrates report layout only. "
                     "In this fictional example, reported profit grew while cash conversion stretched, "
                     "a pattern that would merit triangulation with filings and commentary."),
            significance_json=json.dumps(["Shows how a discovery, counterargument, and falsification condition read together."]),
            key_numbers_json=json.dumps([{"metric": "PAT growth (fictional)", "value": 34.2, "units": "%",
                                          "periods": "FY22→FY24", "formula": "illustrative", "source_ids": []}]),
            timeline_json=json.dumps([{"date": "2024-05-01", "label": "Fictional filing (layout demo)", "kind": "signal"}]),
            counterargument_json=json.dumps({"strongest_alternative": "Fictional one-off",
                                             "why_plausible": "Fixtures have no real alternatives.",
                                             "verdict": "unresolved", "all_alternatives": []}),
            falsification_json=json.dumps({"metric": "cash conversion", "baseline": "fictional",
                                           "condition": "A real run would name the next filing here.",
                                           "period": "next FY", "threshold": "gap narrows >50%"}),
            strength="Weak",
            strength_rationale="Demonstration fixture: no live sources, no calculations. Never cite as research.",
            limitations_json=json.dumps(["Entirely fictional — layout demonstration only."]),
            coverage_json=json.dumps({"n_sources": 0, "fixture": True}),
            created_at="2026-01-01T00:00:00+00:00",
        )
        db.add(d)
        db.commit()
        inv.discovery_id = d.id
        db.commit()
        print(f"demo discovery: /discoveries/{d.id}")
        return d.id
    finally:
        db.close()


if __name__ == "__main__":
    main()
