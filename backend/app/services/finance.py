"""Deterministic financial library (finlib-v1). The LLM is NEVER the calculator of record.

Covers: INR/lakh/crore parsing, fiscal-year normalization (India FY Apr–Mar),
standalone vs consolidated tagging, YoY/QoQ changes, margins, growth CAGR,
peer comparison, missing-value policy (NaN propagation, never imputation),
one-off flagging hooks. All functions pure + unit-tested.
"""
from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd

CODE_VERSION = "finlib-v1"

# ---------- unit parsing ----------

_MULT = {
    "crore": 1.0, "crores": 1.0, "cr": 1.0,
    "lakh": 0.01, "lakhs": 0.01, "lac": 0.01, "lacs": 0.01,
    "million": 0.1, "mn": 0.1,
    "billion": 100.0, "bn": 100.0,
    "thousand": 0.0001, "k": 0.0001,
}


def parse_inr_to_crore(raw: str | float | int | None) -> float:
    """Parse '₹4,521.3 crore' / 'Rs 15200 lakh' / 1234 -> float crore. NaN when unparseable."""
    if raw is None:
        return float("nan")
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace("₹", " ").replace(",", "").lower()
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?|lac|millions?|mn|billions?|bn|thousands?|\bk\b|%)?", s)
    if not m:
        return float("nan")
    val = float(m.group(1))
    unit = (m.group(2) or "").strip()
    if unit == "%":
        return float("nan")  # percents are not currency
    if unit == "":
        # bare number: heuristic — values > 1e6 are likely rupees, convert to crore
        if abs(val) >= 1_000_000:
            return val / 10_000_000
        return float("nan")  # ambiguous bare figure: refuse to guess scale
    return val * _MULT.get(unit, float("nan"))


def parse_percent(raw: str | float | int | None) -> float:
    if raw is None:
        return float("nan")
    if isinstance(raw, (int, float)):
        v = float(raw)
        return v / 100.0 if v > 1.0 else v
    s = str(raw).replace(",", "")
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%?", s)
    if not m:
        return float("nan")
    v = float(m.group(1))
    if "%" in s:
        return v / 100.0
    return v / 100.0 if abs(v) > 1.0 else v


# ---------- fiscal periods (India: FY starts April) ----------

_Q_END_MONTH = {"Q1": 6, "Q2": 9, "Q3": 12, "Q4": 3}


def normalize_period(label: str) -> dict:
    """'Q3 FY24' / 'FY2024' / 'FY24' / '2023-24' -> {fiscal_year, quarter|None, canonical}.

    Canonical forms: 'FY2024' (year ending Mar 2024) or 'FY2024-Q3'.
    """
    s = str(label).upper().replace(" ", "")
    fy = None
    m = re.search(r"FY(\d{2,4})", s)
    if m:
        y = int(m.group(1))
        fy = 2000 + y if y < 100 else y
    else:
        m = re.search(r"(20\d{2})[-/](\d{2,4})", s)
        if m:
            y2 = m.group(2)
            fy = int(y2) if len(y2) == 4 else 2000 + int(y2)
    q = None
    m = re.search(r"Q([1-4])", s)
    if m:
        q = f"Q{m.group(1)}"
    if fy is None:
        return {"fiscal_year": None, "quarter": q, "canonical": str(label), "comparable": False}
    canon = f"FY{fy}" + (f"-{q}" if q else "")
    return {"fiscal_year": fy, "quarter": q, "canonical": canon, "comparable": True}


def periods_comparable(a: str, b: str) -> bool:
    pa, pb = normalize_period(a), normalize_period(b)
    if not pa["comparable"] or not pb["comparable"]:
        return False
    # same granularity only: annual vs annual, or same quarter
    return (pa["quarter"] is None) == (pb["quarter"] is None) and pa["quarter"] == pb["quarter"]


# ---------- deterministic calculations ----------

def _f(x) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def yoy(current: float, prior: float) -> dict:
    c, p = _f(current), _f(prior)
    if not math.isfinite(c) or not math.isfinite(p) or p == 0:
        return {"value": float("nan"), "formula": "(current-prior)/|prior|", "defined": False}
    return {"value": (c - p) / abs(p), "formula": "(current-prior)/|prior|", "defined": True}


def margin(numerator: float, denominator: float) -> dict:
    n, d = _f(numerator), _f(denominator)
    if not math.isfinite(n) or not math.isfinite(d) or d == 0:
        return {"value": float("nan"), "formula": "numerator/denominator", "defined": False}
    return {"value": n / d, "formula": "numerator/denominator", "defined": True}


def cagr(start: float, end: float, periods: float) -> dict:
    s, e = _f(start), _f(end)
    if not math.isfinite(s) or not math.isfinite(e) or s <= 0 or e <= 0 or not periods or periods <= 0:
        return {"value": float("nan"), "formula": "(end/start)^(1/n)-1", "defined": False}
    return {"value": (e / s) ** (1.0 / periods) - 1, "formula": "(end/start)^(1/n)-1", "defined": True}


def series_frame(points: list[dict]) -> pd.DataFrame:
    """points: [{period, value, scope}] -> cleaned frame sorted by fiscal year."""
    rows = []
    for p in points:
        n = normalize_period(str(p.get("period", "")))
        v = _f(p.get("value"))
        if n["fiscal_year"] is None or not math.isfinite(v):
            continue
        rows.append({"fy": n["fiscal_year"], "quarter": n["quarter"], "period": n["canonical"], "value": v, "scope": p.get("scope", "consolidated")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["fy"]).reset_index(drop=True)


def trend_stats(values: list[float]) -> dict:
    v = pd.Series([_f(x) for x in values], dtype=float).dropna()
    if len(v) < 2:
        return {"n": int(len(v)), "direction": "insufficient", "slope_per_period": float("nan"), "last_change": float("nan")}
    x = np.arange(len(v))
    slope = float(np.polyfit(x, v.to_numpy(), 1)[0]) if len(v) >= 2 else float("nan")
    last = float((v.iloc[-1] - v.iloc[-2]) / abs(v.iloc[-2])) if v.iloc[-2] != 0 else float("nan")
    direction = "up" if slope > 0 else ("down" if slope < 0 else "flat")
    return {"n": int(len(v)), "direction": direction, "slope_per_period": slope, "last_change": last}


def anomaly_flags(values: list[float], periods: list[str], thresh_z: float = 2.0) -> list[dict]:
    """Change-point heuristic: z-score of period-over-period changes. Deterministic."""
    v = pd.Series([_f(x) for x in values], dtype=float)
    chg = v.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if len(chg) < 3:
        return []
    mu, sd = float(chg.mean()), float(chg.std(ddof=0))
    if not math.isfinite(sd) or sd == 0:
        return []
    out = []
    for idx, c in chg.items():
        z = (c - mu) / sd
        if abs(z) >= thresh_z:
            out.append({"period": periods[idx] if idx < len(periods) else str(idx), "change": float(c), "z": float(z), "method": f"pct-change z>|{thresh_z}|"})
    return out


def peer_compare(company_val: float, peer_vals: list[float]) -> dict:
    c = _f(company_val)
    peers = [_f(x) for x in peer_vals if math.isfinite(_f(x))]
    if not math.isfinite(c) or not peers:
        return {"defined": False, "rank": None, "median_peer": float("nan"), "diff_vs_median": float("nan")}
    med = float(np.median(peers))
    rank = 1 + sum(1 for p in peers if p > c)
    return {"defined": True, "rank": rank, "of": len(peers) + 1, "median_peer": med, "diff_vs_median": (c - med) / abs(med) if med != 0 else float("nan")}


def fmt_inr_crore(v: float) -> str:
    if not math.isfinite(v):
        return "n/a"
    a = abs(v)
    if a >= 100_000:
        return f"₹{v/100_000:,.2f} lakh cr"
    if a >= 1:
        return f"₹{v:,.1f} cr"
    return f"₹{v*100:,.1f} lakh"


def fmt_pct(v: float) -> str:
    if not math.isfinite(v):
        return "n/a"
    return f"{v*100:+.1f}%" if abs(v) < 10 else f"{v*100:+.0f}%"
