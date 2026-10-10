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


def parse_screener_tables(html: str, default_scope: str = "consolidated") -> dict:
    """Parse ANNUAL tables only: every period column must be `Mar YYYY` (Indian
    annual statements). Quarterly tables (Sep/Dec/Jun quarters) are rejected so
    quarter-ends can never masquerade as fiscal years.

    Returns {key: {label, periods, values, scope}} with scope detected from the
    nearest preceding heading (standalone vs consolidated).
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
            # annual-only: at least 3 `Mar YYYY` columns, zero quarter columns
            annual = [c for c in hcells if re.fullmatch(r"Mar\s+20\d{2}", c.strip(), re.I)]
            quarterly = [c for c in hcells if re.fullmatch(r"(Sep|Dec|Jun)\s+20\d{2}", c.strip(), re.I)]
            if len(annual) < 3 or quarterly:
                continue
            # scope from nearest explicit "Consolidated/Standalone Figures" declaration
            # (the sub-line also links the OTHER view, so plain substring search misfires)
            scope = default_scope
            for prev in tbl.find_all_previous(["p", "h2", "h3", "h4", "div"], limit=15):
                t = (prev.get_text(" ", strip=True) or "")[:200]
                m = re.search(r"(standalone|consolidated)\s+figures", t, re.I)
                if m:
                    scope = m.group(1).lower()
                    break
            body = tbl.find("tbody") or tbl
            for tr in body.find_all("tr"):
                tds = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if len(tds) < 3:
                    continue
                label = re.sub(r"\s+", " ", tds[0]).strip()
                if len(label) < 3 or label.lower().startswith(("note", "source")):
                    continue
                vals = [_num(c) for c in tds[-len(annual):]]
                if sum(1 for v in vals if v == v) < 3:  # need >=3 real annual numbers
                    continue
                key = label.lower()
                if key not in out:  # first (most prominent = consolidated annual) wins
                    out[key] = {"label": label, "periods": [a.strip() for a in annual[-len(vals):]],
                                "values": vals, "scope": scope}
        except Exception:
            continue
    return out


def _label_match(label: str, needles: tuple[str, ...], banned: tuple[str, ...] = ()) -> bool:
    l = " " + re.sub(r"[^a-z%+]", " ", label.lower()) + " "
    if any(b in l for b in banned):
        return False
    return any(re.search(r"(^|[^a-z])" + re.escape(n) + r"([^a-z]|$)", l) for n in needles)


def _pick(tables: dict, scope: str, *needles: str, banned: tuple[str, ...] = ()) -> dict | None:
    # preferred scope first, then any scope
    for want_scope in (scope, None):
        for key, t in tables.items():
            if want_scope and t.get("scope") != want_scope:
                continue
            if _label_match(t["label"], needles, banned):
                return t
    return None


def to_annual_series(tables: dict, ticker: str, url: str) -> list[dict]:
    """Convert parsed tables -> standardized annual series points with provenance.

    Screener P&L figures are in ₹ crore already; balance-sheet too. Tag scope consolidated.
    Returns list of {metric, period(FYxxxx), value, units, scope, url, table}.
    """
    WANT = {
        "revenue": (("sales", "revenue", "total income"), ()),
        "pat": (("net profit", "profit after tax"), ("%", "margin")),
        "ebitda": (("operating profit",), ("margin", "%")),
        "eps": (("eps in rs", "eps"), ("%",)),
        "net_worth": (("net worth", "shareholder funds"), ()),
        "borrowings": (("borrowings", "total debt"), ()),
        "roe": (("roe", "return on equity"), ()),
        "roce": (("roce",), ()),
        "debtor_days": (("debtor days",), ()),
        "inventory_days": (("inventory days",), ()),
        "payable_days": (("payable days",), ()),
        "cash_conversion": (("cash conversion cycle",), ()),
        "opm": (("opm", "operating profit margin"), ()),
    }
    series: list[dict] = []
    seen: set[tuple[str, str, str]] = set()  # (metric, period, scope): never duplicate
    for metric, (needles, banned) in WANT.items():
        t = _pick(tables, "consolidated", *needles, banned=banned)
        if not t:
            continue
        for per, val in zip(t["periods"], t["values"]):
            if val != val:  # NaN
                continue
            m = re.fullmatch(r"Mar\s+(20\d{2})", per.strip(), re.I)
            if not m:
                continue
            period = f"FY{m.group(1)}"
            scope = t.get("scope", "consolidated")
            if (metric, period, scope) in seen:
                continue
            seen.add((metric, period, scope))
            units = "%" if metric in ("roe", "roce", "opm") else ("days" if "days" in metric or "cycle" in metric else ("INR" if metric == "eps" else "INR-cr"))
            series.append({"metric": metric, "period": period, "value": float(val), "units": units,
                           "scope": scope, "url": url, "table": t["label"]})
    return series


def fetch_company_financials(ticker: str) -> dict:
    """Fetch + parse public financials. Returns {ok, url, series, tables_found, error}."""
    url = SCREENER.format(ticker=ticker.upper())
    default_scope = "consolidated" if "consolidated" in url else "standalone"
    got = fetch_url(url)
    if not got.get("ok"):
        return {"ok": False, "url": url, "series": [], "tables_found": 0, "error": got.get("error")}
    try:
        html = got["content"].decode("utf-8", "ignore")
    except Exception:
        return {"ok": False, "url": url, "series": [], "tables_found": 0, "error": "decode failed"}
    tables = parse_screener_tables(html, default_scope)
    series = to_annual_series(tables, ticker, url)
    return {"ok": True, "url": url, "series": series, "tables_found": len(tables),
            "error": "" if series else "parsed tables but found no usable annual series"}
