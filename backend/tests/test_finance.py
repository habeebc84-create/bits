import math

from app.services import finance as F


def test_parse_inr_units():
    assert F.parse_inr_to_crore("₹4,521.3 crore") == 4521.3
    assert F.parse_inr_to_crore("Rs 15200 lakh") == 152.0
    assert F.parse_inr_to_crore("₹2.5 billion") == 250.0
    assert math.isnan(F.parse_inr_to_crore("n/a"))
    assert math.isnan(F.parse_inr_to_crore("12.5%"))  # percents refused as currency
    assert math.isnan(F.parse_inr_to_crore("4521"))  # ambiguous bare figure refused


def test_fiscal_normalization():
    assert F.normalize_period("Q3 FY24")["canonical"] == "FY2024-Q3"
    assert F.normalize_period("FY2024")["canonical"] == "FY2024"
    assert F.normalize_period("2023-24")["fiscal_year"] == 2024
    assert F.periods_comparable("FY2023", "FY2024")
    assert F.periods_comparable("Q3 FY23", "Q3 FY24")
    assert not F.periods_comparable("FY2024", "Q3 FY24")  # granularity mismatch
    assert not F.periods_comparable("TTM", "FY2024")


def test_yoy_margin_cagr_missing():
    r = F.yoy(120, 100)
    assert r["defined"] and abs(r["value"] - 0.2) < 1e-9
    assert not F.yoy(100, 0)["defined"]
    assert not F.yoy(float("nan"), 100)["defined"]  # NaN propagates, never imputed
    m = F.margin(20, 100)
    assert m["defined"] and abs(m["value"] - 0.2) < 1e-9
    assert not F.margin(20, 0)["defined"]
    c = F.cagr(100, 133.1, 3)
    assert c["defined"] and abs(c["value"] - 0.10) < 0.01
    assert not F.cagr(-5, 10, 2)["defined"]


def test_anomaly_and_trend():
    vals = [100, 101, 100, 102, 101, 102, 250, 103]
    pers = [f"FY{2019 + i}" for i in range(8)]
    flags = F.anomaly_flags(vals, pers)
    assert any(f["period"] == "FY2025" for f in flags)
    t = F.trend_stats([10, 20, 30])
    assert t["direction"] == "up"
    assert F.trend_stats([5])["direction"] == "insufficient"


def test_peer_compare():
    r = F.peer_compare(0.2, [0.1, 0.15, 0.25])
    assert r["defined"] and r["rank"] == 2 and r["of"] == 4
    assert not F.peer_compare(float("nan"), [0.1])["defined"]
