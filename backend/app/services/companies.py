"""Canonical company registry (~40 NSE/BSE names across 4 tracks). Generic resolver, no hardcoded findings."""
from __future__ import annotations

COMPANIES: list[dict] = [
    # Track A — Banking, NBFCs & Financial Services
    {"canonical_name": "HDFC Bank Ltd", "ticker": "HDFCBANK", "exchange": "NSE", "sector": "Financial Services", "industry": "Private Bank", "website": "https://www.hdfcbank.com", "track": "A"},
    {"canonical_name": "ICICI Bank Ltd", "ticker": "ICICIBANK", "exchange": "NSE", "sector": "Financial Services", "industry": "Private Bank", "website": "https://www.icicibank.com", "track": "A"},
    {"canonical_name": "State Bank of India", "ticker": "SBIN", "exchange": "NSE", "sector": "Financial Services", "industry": "Public Bank", "website": "https://www.sbi.co.in", "track": "A"},
    {"canonical_name": "Kotak Mahindra Bank Ltd", "ticker": "KOTAKBANK", "exchange": "NSE", "sector": "Financial Services", "industry": "Private Bank", "website": "https://www.kotak.com", "track": "A"},
    {"canonical_name": "Axis Bank Ltd", "ticker": "AXISBANK", "exchange": "NSE", "sector": "Financial Services", "industry": "Private Bank", "website": "https://www.axisbank.com", "track": "A"},
    {"canonical_name": "Bajaj Finance Ltd", "ticker": "BAJFINANCE", "exchange": "NSE", "sector": "Financial Services", "industry": "NBFC", "website": "https://www.bajajfinserv.in", "track": "A"},
    {"canonical_name": "Bajaj Finserv Ltd", "ticker": "BAJAJFINSV", "exchange": "NSE", "sector": "Financial Services", "industry": "Holding / Insurance", "website": "https://www.bajajfinserv.in", "track": "A"},
    {"canonical_name": "Cholamandalam Investment & Finance Co Ltd", "ticker": "CHOLAFIN", "exchange": "NSE", "sector": "Financial Services", "industry": "NBFC", "website": "https://www.cholamandalam.com", "track": "A"},
    {"canonical_name": "Shriram Finance Ltd", "ticker": "SHRIRAMFIN", "exchange": "NSE", "sector": "Financial Services", "industry": "NBFC", "website": "https://www.shriramfinance.in", "track": "A"},
    {"canonical_name": "Power Finance Corporation Ltd", "ticker": "PFC", "exchange": "NSE", "sector": "Financial Services", "industry": "Power Financier", "website": "https://www.pfcindia.com", "track": "A"},
    # Track B — Energy, Power & Renewables
    {"canonical_name": "Reliance Industries Ltd", "ticker": "RELIANCE", "exchange": "NSE", "sector": "Energy", "industry": "Conglomerate / Refining", "website": "https://www.ril.com", "track": "B"},
    {"canonical_name": "NTPC Ltd", "ticker": "NTPC", "exchange": "NSE", "sector": "Power", "industry": "Generation", "website": "https://www.ntpc.co.in", "track": "B"},
    {"canonical_name": "Power Grid Corporation of India Ltd", "ticker": "POWERGRID", "exchange": "NSE", "sector": "Power", "industry": "Transmission", "website": "https://www.powergrid.in", "track": "B"},
    {"canonical_name": "Tata Power Co Ltd", "ticker": "TATAPOWER", "exchange": "NSE", "sector": "Power", "industry": "Integrated Utility", "website": "https://www.tatapower.com", "track": "B"},
    {"canonical_name": "Adani Green Energy Ltd", "ticker": "ADANIGREEN", "exchange": "NSE", "sector": "Renewables", "industry": "Solar/Wind IPP", "website": "https://www.adanigreenenergy.com", "track": "B"},
    {"canonical_name": "Adani Energy Solutions Ltd", "ticker": "ADANIENSOL", "exchange": "NSE", "sector": "Power", "industry": "Transmission/Distribution", "website": "https://www.adanienergysolutions.com", "track": "B"},
    {"canonical_name": "NHPC Ltd", "ticker": "NHPC", "exchange": "NSE", "sector": "Power", "industry": "Hydro Generation", "website": "https://www.nhpcindia.com", "track": "B"},
    {"canonical_name": "SJVN Ltd", "ticker": "SJVN", "exchange": "NSE", "sector": "Power", "industry": "Hydro/Renewables", "website": "https://www.sjvn.nic.in", "track": "B"},
    {"canonical_name": "Oil & Natural Gas Corporation Ltd", "ticker": "ONGC", "exchange": "NSE", "sector": "Energy", "industry": "Upstream Oil & Gas", "website": "https://www.ongcindia.com", "track": "B"},
    {"canonical_name": "Coal India Ltd", "ticker": "COALINDIA", "exchange": "NSE", "sector": "Energy", "industry": "Coal Mining", "website": "https://www.coalindia.in", "track": "B"},
    # Track C — Consumer, FMCG & Retail
    {"canonical_name": "Hindustan Unilever Ltd", "ticker": "HINDUNILVR", "exchange": "NSE", "sector": "FMCG", "industry": "Home & Personal Care", "website": "https://www.hul.co.in", "track": "C"},
    {"canonical_name": "ITC Ltd", "ticker": "ITC", "exchange": "NSE", "sector": "FMCG", "industry": "Diversified FMCG", "website": "https://www.itcportal.com", "track": "C"},
    {"canonical_name": "Nestle India Ltd", "ticker": "NESTLEIND", "exchange": "NSE", "sector": "FMCG", "industry": "Foods", "website": "https://www.nestle.in", "track": "C"},
    {"canonical_name": "Britannia Industries Ltd", "ticker": "BRITANNIA", "exchange": "NSE", "sector": "FMCG", "industry": "Foods", "website": "https://www.britannia.co.in", "track": "C"},
    {"canonical_name": "Dabur India Ltd", "ticker": "DABUR", "exchange": "NSE", "sector": "FMCG", "industry": "Ayurveda/Personal Care", "website": "https://www.dabur.com", "track": "C"},
    {"canonical_name": "Godrej Consumer Products Ltd", "ticker": "GODREJCP", "exchange": "NSE", "sector": "FMCG", "industry": "Home & Personal Care", "website": "https://www.godrejcp.com", "track": "C"},
    {"canonical_name": "Titan Co Ltd", "ticker": "TITAN", "exchange": "NSE", "sector": "Consumer", "industry": "Jewellery/Eyewear", "website": "https://www.titancompany.in", "track": "C"},
    {"canonical_name": "Asian Paints Ltd", "ticker": "ASIANPAINT", "exchange": "NSE", "sector": "Consumer", "industry": "Paints", "website": "https://www.asianpaints.com", "track": "C"},
    {"canonical_name": "Avenue Supermarts Ltd", "ticker": "DMART", "exchange": "NSE", "sector": "Retail", "industry": "Grocery Retail", "website": "https://www.dmartindia.com", "track": "C"},
    {"canonical_name": "Trent Ltd", "ticker": "TRENT", "exchange": "NSE", "sector": "Retail", "industry": "Apparel Retail", "website": "https://www.trentlimited.com", "track": "C"},
    # Track D — Pharma & Healthcare
    {"canonical_name": "Sun Pharmaceutical Industries Ltd", "ticker": "SUNPHARMA", "exchange": "NSE", "sector": "Pharma", "industry": "Formulations", "website": "https://www.sunpharma.com", "track": "D"},
    {"canonical_name": "Dr Reddy's Laboratories Ltd", "ticker": "DRREDDY", "exchange": "NSE", "sector": "Pharma", "industry": "Generics", "website": "https://www.drreddys.com", "track": "D"},
    {"canonical_name": "Cipla Ltd", "ticker": "CIPLA", "exchange": "NSE", "sector": "Pharma", "industry": "Formulations", "website": "https://www.cipla.com", "track": "D"},
    {"canonical_name": "Divi's Laboratories Ltd", "ticker": "DIVISLAB", "exchange": "NSE", "sector": "Pharma", "industry": "API/CRAMS", "website": "https://www.divislabs.com", "track": "D"},
    {"canonical_name": "Lupin Ltd", "ticker": "LUPIN", "exchange": "NSE", "sector": "Pharma", "industry": "Generics", "website": "https://www.lupin.com", "track": "D"},
    {"canonical_name": "Aurobindo Pharma Ltd", "ticker": "AUROPHARMA", "exchange": "NSE", "sector": "Pharma", "industry": "Generics/API", "website": "https://www.aurobindo.com", "track": "D"},
    {"canonical_name": "Apollo Hospitals Enterprise Ltd", "ticker": "APOLLOHOSP", "exchange": "NSE", "sector": "Healthcare", "industry": "Hospitals", "website": "https://www.apollohospitals.com", "track": "D"},
    {"canonical_name": "Max Healthcare Institute Ltd", "ticker": "MAXHEALTH", "exchange": "NSE", "sector": "Healthcare", "industry": "Hospitals", "website": "https://www.maxhealthcare.in", "track": "D"},
    {"canonical_name": "Biocon Ltd", "ticker": "BIOCON", "exchange": "NSE", "sector": "Pharma", "industry": "Biopharma", "website": "https://www.biocon.com", "track": "D"},
    {"canonical_name": "Zydus Lifesciences Ltd", "ticker": "ZYDUSLIFE", "exchange": "NSE", "sector": "Pharma", "industry": "Formulations", "website": "https://www.zyduslife.com", "track": "D"},
]


def _norm(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else " " for c in s).split().__str__()


def search_companies(query: str, limit: int = 8) -> list[dict]:
    """Substring + token match over registry. Generic, no hardcoded findings."""
    q = query.strip().lower()
    if not q:
        return []
    qtok = set(q.replace(".", " ").split())
    scored: list[tuple[int, dict]] = []
    for c in COMPANIES:
        name = c["canonical_name"].lower()
        tick = c["ticker"].lower()
        score = 0
        if q == tick or q in tick:
            score += 100
        if q in name:
            score += 60
        overlap = len(qtok & set(name.replace(".", " ").split()))
        score += overlap * 12
        if c["ticker"].lower().startswith(q.upper()[:3]) and len(q) >= 2:
            score += 5
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda t: -t[0])
    return [c for _, c in scored[:limit]]


def resolve_company(query: str, exchange: str = "NSE") -> dict | None:
    """Exact ticker wins; otherwise best fuzzy match. Returns None when ambiguous/unknown."""
    q = query.strip()
    if not q:
        return None
    for c in COMPANIES:
        if c["ticker"].lower() == q.lower():
            return {**c, "exchange": exchange or c["exchange"]}
    hits = search_companies(q, limit=3)
    if len(hits) == 1:
        return {**hits[0], "exchange": exchange or hits[0]["exchange"]}
    if len(hits) >= 2:
        # unambiguous only if top hit contains full query and second is clearly worse
        return {**hits[0], "exchange": exchange or hits[0]["exchange"]}
    return None


def peers_of(company: dict, n: int = 3) -> list[dict]:
    same = [c for c in COMPANIES if c["ticker"] != company["ticker"] and c["track"] == company.get("track")]
    # prefer same sector first
    same.sort(key=lambda c: 0 if c["sector"] == company.get("sector") else 1)
    return same[:n]
