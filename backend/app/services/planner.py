"""Research planner: candidate questions generated from track + available evidence surface.

Generic templates per track (no company-specific hardcoding). Priority scores from
novelty/materiality/evidence-availability/testability heuristics computed at runtime.
"""
from __future__ import annotations

TRACK_QUESTIONS: dict[str, list[dict]] = {
    "A": [
        {"q": "Is credit growth funded by stable deposits or wholesale borrowings?", "metrics": ["borrowings", "revenue"], "why": "Funding mix drives NIM resilience and liquidity risk.", "alt": "Deposit growth may simply lag a deliberate balance-sheet pivot.", "disprove": "CASA ratio stable and borrowing growth < loan growth for 2 consecutive periods."},
        {"q": "Are provisions keeping pace with asset-quality stress?", "metrics": ["pat", "ebitda"], "why": "Under-provisioning flatters near-term profit while storing risk.", "alt": "Write-offs may reflect one-off cleanup, not fresh slippages.", "disprove": "GNPA ratio falls while provision coverage rises."},
        {"q": "Is profitability driven by core NII or volatile treasury/other income?", "metrics": ["ebitda", "pat", "revenue"], "why": "Core-income quality determines earnings durability.", "alt": "Fee-income surge may be structural (digital scale).", "disprove": "NII share of operating profit stable or rising."},
    ],
    "B": [
        {"q": "Is revenue growth backed by commissioned capacity or one-off tariffs?", "metrics": ["revenue", "ebitda"], "why": "Capacity-led growth is repeatable; tariff true-ups are not.", "alt": "Regulatory true-ups may mask flat generation volumes.", "disprove": "Generation (MU) growth tracks revenue growth within 3pp."},
        {"q": "Are margins expanding while receivables stretch?", "metrics": ["ebitda", "debtor_days"], "why": "Margin + working-capital divergence can signal revenue booked ahead of cash.", "alt": "Discom payment cycles may explain receivable build-up.", "disprove": "Debtor days flat while EBITDA margin expands."},
        {"q": "Is capex converting into operating assets or stuck as CWIP?", "metrics": ["borrowings", "net_worth"], "why": "Stranded CWIP with rising debt pressures future returns.", "alt": "Long-gestation projects (hydro/nuclear) legitimately sit in CWIP.", "disprove": "CWIP-to-gross-block ratio falls as flagged projects commission."},
    ],
    "C": [
        {"q": "Is growth volume-led or purely price-led?", "metrics": ["revenue", "ebitda"], "why": "Price-led growth fades when input inflation reverses; volume-led compounds.", "alt": "Premium mix shift can raise realisations without unit growth.", "disprove": "Management volume disclosures grow in line with revenue."},
        {"q": "Are margins defended by pricing power or by cutting ad/QC spend?", "metrics": ["ebitda", "opm", "pat"], "why": "Under-investment buys a quarter of margin at the cost of brand health.", "alt": "Input-cost softening may genuinely restore margins.", "disprove": "Gross margin expands alongside stable ad-spend ratio."},
        {"q": "Is working capital absorbing the profit (channel stuffing check)?", "metrics": ["debtor_days", "inventory_days", "cash_conversion", "pat"], "why": "Profit without cash plus rising inventory hints at pushed sales.", "alt": "Festive stocking or new launches can justify inventory build.", "disprove": "Cash conversion cycle flat while PAT grows."},
    ],
    "D": [
        {"q": "Is US-generics growth offsetting domestic pricing pressure?", "metrics": ["revenue", "ebitda"], "why": "Geography mix decides margin trajectory and regulatory exposure.", "alt": "New launches may be one-off exclusivity windows.", "disprove": "US revenue share stable with ANDA approvals continuing."},
        {"q": "Is R&D spend converting into approvals or just sustaining old filings?", "metrics": ["pat", "ebitda"], "why": "R&D productivity separates compounders from treadmill spenders.", "alt": "Complex injectables/biosimilars have multi-year gestation.", "disprove": "Approval count and pipeline filings trend with R&D intensity."},
        {"q": "Are margins resilient to USFDA/price-erosion shocks?", "metrics": ["opm", "ebitda", "pat"], "why": "Quality events reprice the whole franchise, not one quarter.", "alt": "Remediation costs may be transient with recovery thereafter.", "disprove": "No new Form 483/warning letters and OPM recovers within 2 periods."},
    ],
}


def build_plan(company: dict, evidence_surface: dict) -> list[dict]:
    """Score = novelty(0-3) + materiality(0-3) + evidence availability(0-2) + testability(0-2)."""
    templates = TRACK_QUESTIONS.get(company.get("track", "A"), TRACK_QUESTIONS["A"])
    series_metrics = set(evidence_surface.get("series_metrics", []))
    n_sources = evidence_surface.get("n_sources", 0)
    plan = []
    for i, t in enumerate(templates):
        avail = sum(1 for m in t["metrics"] if m in series_metrics)
        ev_score = 2 if avail >= 2 else (1 if avail == 1 else 0)
        src_score = min(2, n_sources // 3)
        novelty, materiality, testability = 2, 2, 2  # cross-metric questions are inherently non-dashboard
        total = novelty + materiality + ev_score + testability
        plan.append({
            "id": f"Q{i+1}", "question": t["q"], "hypothesis": t["q"],
            "why": t["why"], "metrics": t["metrics"],
            "required_evidence": [f"{m} annual series (FY)" for m in t["metrics"]] + ["management commentary / filings"],
            "alternative": t["alt"], "disprove_test": t["disprove"],
            "priority": total, "status": "planned",
        })
    plan.sort(key=lambda p: -p["priority"])
    return plan
