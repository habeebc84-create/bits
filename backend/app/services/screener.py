"""Financial-statement ingestion from public pages (Screener.in company pages are public,
plus generic table parsing). All numbers carry provenance {url, table, period, scope}.

Never invents figures: returns only what was parsed, with scope + period tags.
"""
from __future__ import annotations

import logging
import re

from . import finance as F
from .fetcher import fetch_url

log = logging.getLogger("signalhunter.screener")

SCREENER = "https://www.screener.in/company/{ticker}/consolidated/"


def _num(cell: str) -> float:
    s = cell.replace(",", "").strip()
    if s in ("", "-", "--", "NA", "N/A", "—"):
        return float("nan")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else float("nan")


def parse_screener_tables(html: str) -> dict:
    """Parse Screener-style data tables: {Narration: [v_oldest..v_latest], periods:[...]}.

    Generic: works on any <table> with a header row of periods (Mar YYYY / FY).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}
    soup = BeautifulSoup(html, "lxml")
    out: dict = {}
    for tbl in soup.find_all("table"):
        try:
            head = tbl.find("thead")
            if not head:
                continue
            hcells = [c.get_text(" ", strip=True) for c in head.find_all(["th", "td"])]
            # period columns look like 'Mar 2021' .. 'Mar 2025' or TTM
            periods = [c for c in hcells if re.search(r"(Mar|Dec|Sep|Jun)\s+20\d{2}|TTM|FY", c, re.I)]
            if len(periods) < 2:
                continue
            body = tbl.find("tbody") or tbl
            for tr in body.find_all("tr"):
                tds = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if len(tds) < 3:
                    continue
                label = re.sub(r"\s+", " ", tds[0]).strip()
                if len(label) < 3 or label.lower().startswith(("note", "source")):
                    continue
                # align: last len(periods) cells
                vals = [_num(c) for c in tds[-len(periods):]]
                if sum(1 for v in vals if v == v) < 2:  # need >=2 real numbers
                    continue
                key = label.lower()
                if key not in out:  # first (most prominent) table wins per metric
                    out[key] = {"label": label, "periods": periods[-len(vals):], "values": vals}
        except Exception:
            continue
    return out


def _pick(tables: dict, *needles: str) -> dict | None:
    for key, t in tables.items():
        if any(n in key for n in needles):
            return t
    return None


def to_annual_series(tables: dict, ticker: str, url: str) -> list[dict]:
    """Convert parsed tables -> standardized annual series points with provenance.

    Screener P&L figures are in ₹ crore already; balance-sheet too. Tag scope consolidated.
    Returns list of {metric, period(FYxxxx), value, units, scope, url, table}.
    """
    WANT = {
        "revenue": ("sales", "revenue", "total income", "income"),
        "pat": ("net profit", "profit after tax"),
        "ebitda": ("operating profit",),
        "eps": ("eps in rs", "eps"),
        "net_worth": ("net worth", "shareholder", "equity"),
        "borrowings": ("borrowings", "total debt", "debt"),
        "roe": ("roe %", "return on equity"),
        "roce": ("roce %",),
        "debtor_days": ("debtor days",),
        "inventory_days": ("inventory days",),
        "payable_days": ("payable days",),
        "cash_conversion": ("cash conversion cycle",),
        "opm": ("opm %", "operating profit margin"),
    }
    series: list[dict] = []
    for metric, needles in WANT.items():
        t = _pick(tables, *needles)
        if not t:
            continue
        for per, val in zip(t["periods"], t["values"]):
            if val != val:  # NaN
                continue
            m = re.search(r"(Mar|Dec|Sep|Jun)?\s*(20\d{2})", per)
            if not m and per.upper() != "TTM":
                continue
            if per.upper() == "TTM":
                period = "TTM"
            else:
                yy = int(m.group(2))
                # Screener 'Mar YYYY' == FY ending Mar YYYY
                period = f"FY{yy}"
            units = "%" if metric in ("roe", "roce", "opm") else ("days" if "days" in metric or "cycle" in metric else ("INR" if metric == "eps" else "INR-cr"))
            series.append({"metric": metric, "period": period, "value": float(val), "units": units,
                           "scope": "consolidated", "url": url, "table": t["label"]})
    return series


def fetch_company_financials(ticker: str) -> dict:
    """Fetch + parse public financials. Returns {ok, url, series, tables_found, error}."""
    url = SCREENER.format(ticker=ticker.upper())
    got = fetch_url(url)
    if not got.get("ok"):
        return {"ok": False, "url": url, "series": [], "tables_found": 0, "error": got.get("error")}
    try:
        html = got["content"].decode("utf-8", "ignore")
    except Exception:
        return {"ok": False, "url": url, "series": [], "tables_found": 0, "error": "decode failed"}
    tables = parse_screener_tables(html)
    series = to_annual_series(tables, ticker, url)
    return {"ok": True, "url": url, "series": series, "tables_found": len(tables),
            "error": "" if series else "parsed tables but found no usable annual series"}
