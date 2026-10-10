from app.services.analysis import assess_strength, adversarial_review
from app.services.companies import resolve_company, search_companies
from app.services.fetcher import canonicalize, dedupe_sources
from app.services.planner import build_plan


def test_dedupe_canonical_and_hash():
    items = [
        {"url": "https://x.com/a?utm_source=foo", "content_hash": "h1"},
        {"url": "https://x.com/a", "content_hash": "h1"},
        {"url": "https://y.com/b", "content_hash": "h2"},
    ]
    out = dedupe_sources(items)
    assert len(out) == 2
    assert canonicalize("https://X.com/a/?utm_source=z") == "https://x.com/a"


def test_company_resolution_generic():
    assert resolve_company("HDFCBANK")["ticker"] == "HDFCBANK"
    assert resolve_company("hdfc bank")["ticker"] == "HDFCBANK"
    assert resolve_company("ZZZNOTACOMPANYXYZ") is None or isinstance(resolve_company("ZZZNOTACOMPANYXYZ"), dict)
    hits = search_companies("sun pharma")
    assert hits and hits[0]["ticker"] == "SUNPHARMA"


def test_plan_scored_and_generic():
    plan = build_plan({"ticker": "ITC", "track": "C"}, {"series_metrics": ["revenue", "pat"], "n_sources": 6})
    assert len(plan) == 3
    assert all(p["priority"] >= 0 for p in plan)
    assert all(p.get("disprove_test") for p in plan)


def test_period_window_and_divergence():
    from app.services.analysis import detect_patterns, _year_window
    assert _year_window("FY2022-FY2025") == (2022, 2025)
    assert _year_window("all") is None
    series = [
        {"metric": "revenue", "period": f"FY{y}", "value": v, "units": "INR-cr", "table": "Sales", "scope": "consolidated"}
        for y, v in zip(range(2019, 2026), [100, 110, 120, 130, 140, 400, 500])
    ] + [
        {"metric": "pat", "period": f"FY{y}", "value": v, "units": "INR-cr", "table": "Net Profit", "scope": "consolidated"}
        for y, v in zip(range(2019, 2026), [10, 11, 12, 13, 14, 15, 16])
    ]
    pats = detect_patterns(series, "C", "FY2022-FY2025")
    div = [p for p in pats if p["kind"] == "divergence"]
    assert div, "revenue up vs pat ~flat must diverge"
    # window respected: no period outside FY2022-FY2025
    for p in div:
        assert all(2022 <= int(x[2:]) <= 2025 for x in p["periods"])


def test_adversarial_and_strength_rules():
    c = adversarial_review({"text": "x"}, [], 1, False)
    assert c["strongest_alternative"] and c["verdict"] in ("ruled_out", "unresolved", "changes_interpretation")
    s, _ = assess_strength(4, True, {}, {"verdict": "ruled_out", "strongest_alternative": "t"}, [])
    assert s == "Strong"
    s2, _ = assess_strength(1, True, {}, {"verdict": "unresolved", "strongest_alternative": "t"}, ["a", "b", "c", "d"])
    assert s2 == "Weak"  # never inflated
    # unresolved alternative caps a many-line finding at Moderate, not Strong
    s3, _ = assess_strength(9, True, {}, {"verdict": "unresolved", "strongest_alternative": "sector-wide effect"}, [])
    assert s3 == "Moderate"


def test_claim_validation_no_fabrication():
    # evidence passages must be verbatim substrings: simulate validator rule
    text = "Revenue from operations grew 12% to Rs 500 crore in FY24."
    from app.services.fetcher import extract_passages
    ps = extract_passages(text)
    assert ps and all(p["passage"] in text for p in ps)
