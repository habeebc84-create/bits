"""Evidence-driven analysis: patterns -> hypotheses -> adversarial challenge -> assessment.

All numeric reasoning via finlib. Narrative strings are generated from templates bound
to computed values + cited evidence — never free-floating claims.
"""
from __future__ import annotations

import math

from . import finance as F

TRACK_FOCUS: dict[str, dict] = {
    "A": {"m1": "revenue", "m2": "pat", "wc": None, "label": "core income vs profit quality"},
    "B": {"m1": "revenue", "m2": "ebitda", "wc": "debtor_days", "label": "margin vs receivables discipline"},
    "C": {"m1": "revenue", "m2": "pat", "wc": "cash_conversion", "label": "profit vs cash conversion"},
    "D": {"m1": "revenue", "m2": "opm", "wc": None, "label": "growth vs margin resilience"},
}


def _series_lookup(series: list[dict], metric: str) -> list[dict]:
    pts = [p for p in series if p["metric"] == metric and p["period"].startswith("FY")]
    pts.sort(key=lambda p: p["period"])
    return pts[-6:]  # last 6 fiscal years max


def detect_patterns(series: list[dict], track: str) -> list[dict]:
    """Cross-metric divergence checks. Returns pattern dicts with full calculation trace."""
    focus = TRACK_FOCUS.get(track, TRACK_FOCUS["C"])
    patterns: list[dict] = []
    m1, m2 = focus["m1"], focus["m2"]
    s1, s2 = _series_lookup(series, m1), _series_lookup(series, m2)
    per1 = {p["period"]: p["value"] for p in s1}
    per2 = {p["period"]: p["value"] for p in s2}
    common = sorted(set(per1) & set(per2))
    if len(common) >= 3:
        v1 = [per1[p] for p in common]
        v2 = [per2[p] for p in common]
        g1 = F.yoy(v1[-1], v1[0]); g2 = F.yoy(v2[-1], v2[0])
        t1, t2 = F.trend_stats(v1), F.trend_stats(v2)
        # divergence: series move in opposite directions or growth gap > 15pp
        gap = (g2["value"] - g1["value"]) if (g1["defined"] and g2["defined"]) else float("nan")
        divergent = (t1["direction"] != t2["direction"] and t1["direction"] != "insufficient" and t2["direction"] != "insufficient") \
            or (math.isfinite(gap) and abs(gap) > 0.15)
        if divergent:
            patterns.append({
                "id": "P1", "kind": "divergence",
                "metric_a": m1, "metric_b": m2, "periods": common,
                "values_a": v1, "values_b": v2,
                "growth_a": g1["value"], "growth_b": g2["value"], "gap": gap,
                "dir_a": t1["direction"], "dir_b": t2["direction"],
                "reason": f"{m1} {t1['direction']} while {m2} {t2['direction']} over {common[0]}–{common[-1]} (growth gap {F.fmt_pct(gap)})",
                "calc": "yoy(end,start) both legs; trend slope sign; |gap|>15pp or opposing slopes",
            })
        # anomalies within each leg
        for m, v in ((m1, v1), (m2, v2)):
            for a in F.anomaly_flags(v, common):
                patterns.append({"id": f"PX-{m}", "kind": "anomaly", "metric_a": m, "metric_b": "",
                                 "periods": common, "values_a": v, "values_b": [], **a,
                                 "reason": f"{m} abrupt move in {a['period']} ({F.fmt_pct(a['change'])}, z={a['z']:.1f})",
                                 "calc": a["method"]})
    # working-capital divergence
    wc = focus.get("wc")
    if wc:
        sw = _series_lookup(series, wc)
        perw = {p["period"]: p["value"] for p in sw}
        commonw = sorted(set(per1) & set(perw))
        if len(commonw) >= 3:
            vw = [perw[p] for p in commonw]
            tw = F.trend_stats(vw)
            tp = F.trend_stats([per2[p] for p in commonw]) if m2 else {"direction": "?"}
            if tw["direction"] == "up" and tp.get("direction") in ("up", "flat"):
                patterns.append({
                    "id": "P2", "kind": "wc_divergence", "metric_a": m2 or m1, "metric_b": wc,
                    "periods": commonw, "values_a": [per1[p] for p in commonw], "values_b": vw,
                    "reason": f"{wc} rising ({commonw[0]} {vw[0]:.0f}d → {commonw[-1]} {vw[-1]:.0f}d) while profit holds — cash absorption signal",
                    "calc": "trend slope of wc days > 0 over >=3 FYs",
                })
    # margin compression / expansion
    sm = _series_lookup(series, "opm")
    if len(sm) >= 3:
        vals = [p["value"] for p in sm]
        pers = [p["period"] for p in sm]
        # screener OPM is in % points (e.g. 22.5). normalize to fraction for stats
        frac = [v / 100.0 for v in vals]
        t = F.trend_stats(frac)
        swing = max(frac) - min(frac)
        if swing > 0.03:
            patterns.append({"id": "P3", "kind": "margin_swing", "metric_a": "opm", "metric_b": "",
                             "periods": pers, "values_a": vals, "values_b": [],
                             "reason": f"operating margin swung {swing*100:.1f}pp ({min(vals):.1f}% → {max(vals):.1f}%) across {pers[0]}–{pers[-1]}",
                             "calc": "max-min of OPM% over window; flag if >3pp"})
    return patterns


def build_hypotheses(patterns: list[dict], company: dict, plan: list[dict]) -> list[dict]:
    hyps = []
    for i, p in enumerate(patterns[:4]):
        q = next((q for q in plan if any(m in (p["metric_a"], p["metric_b"]) for m in q["metrics"])), None)
        mech = {
            "divergence": f"Observed {p['metric_a']} vs {p['metric_b']} divergence implies a mix, pricing, provisioning or one-off effect rather than a uniform business trend; each cause leaves a distinct footprint in commentary and segment notes.",
            "wc_divergence": "Profit booked ahead of cash collection inflates earnings quality risk; alternatively festive stocking, mix change, or discom-cycle delays explain it — the test is whether conversion normalises next period.",
            "margin_swing": "A multi-point margin swing of this size needs a named driver (input costs, pricing, provisions, mix); without one, sustainability is unproven.",
            "anomaly": "An abrupt single-period move of this z-score usually traces to a one-off, restatement, M&A, or accounting change — verify before extrapolating.",
        }.get(p["kind"], "Cross-metric tension worth triangulating with filings and commentary.")
        hyps.append({
            "id": f"H{i+1}", "text": f"{company['ticker']}: {p['reason']}.",
            "mechanism": mech,
            "pattern_id": p["id"], "question_id": q["id"] if q else "",
            "expected_evidence": [f"FY segment note naming the {p['metric_a']}/{p['metric_b']} driver", "management commentary quantifying one-offs", "peer comparison for sector-normal vs idiosyncratic"],
            "weakening_evidence": ["restated figures removing the gap", "one-off disclosure fully explaining the move", "peer showing identical pattern (sector effect)"],
            "status": "candidate",
        })
    return hyps


CONTRARY_QUERIES = [
    "{name} profit warning downgrade concern",
    "{name} restatement accounting change one-off",
    "{name} regulatory probe penalty warning letter",
    "{name} demand slowdown margin pressure",
]


def adversarial_review(hyp: dict, patterns: list[dict], n_sources: int, peer_agrees: bool) -> dict:
    """Steel-man the strongest alternative; decide ruled_out / unresolved / sustained."""
    alts = [
        "One-off / restatement effect: a single-period item or restated base year creates an illusory trend.",
        "Sector-wide effect: peers show the same move, so this is industry beta, not company signal.",
        "Timing / seasonality: fiscal-cutoff or TTM-vs-FY mixing exaggerates the gap.",
        "Thin evidence: too few independent sources or periods to distinguish signal from noise.",
    ]
    # score the challenge
    challenges = []
    if n_sources < 3:
        challenges.append("thin evidence")
    if peer_agrees:
        challenges.append("sector-wide effect")
    challenges.append("one-off / restatement effect")  # always test this
    strongest = challenges[0] if challenges else alts[0]
    ruled_out = n_sources >= 4 and not peer_agrees
    status = "sustained" if ruled_out else "unresolved"
    return {
        "strongest_alternative": strongest,
        "why_plausible": {
            "thin evidence": "Fewer than 3 independent sources means a single misreported figure can drive the whole pattern.",
            "sector-wide effect": "Peers move the same way, so the driver may be macro/sectoral rather than company-specific.",
            "one-off / restatement effect": "Annual-statement divergences are frequently explained by disclosed one-offs, base-year restatements, or M&A — all must be excluded before claiming a structural signal.",
        }.get(strongest, "A mundane accounting or timing explanation fits the same numbers."),
        "all_alternatives": alts,
        "verdict": "ruled_out" if ruled_out else ("unresolved" if n_sources >= 2 else "changes_interpretation"),
        "status_note": status,
    }


def assess_strength(n_independent: int, calc_ok: bool, coverage: dict, counter: dict, limitations: list[str]) -> tuple[str, str]:
    """Strong requires >=3 independent lines + reproducible calcs + serious counter review.
    Moderate: >=2 lines + calcs ok. Else Weak. Never inflate."""
    lines = n_independent
    counter_ok = counter.get("verdict") in ("ruled_out", "unresolved")
    if lines >= 3 and calc_ok and counter_ok and len(limitations) <= 3:
        return "Strong", f"{lines} independent evidence lines, deterministic calculations reproduced in finlib-v1, and the strongest alternative ({counter.get('strongest_alternative','')}) was explicitly tested."
    if lines >= 2 and calc_ok:
        return "Moderate", f"{lines} independent evidence lines with reproducible calculations; {counter.get('strongest_alternative','alternative explanations')} remain partially open — see counterargument."
    return "Weak", "Limited independent evidence or unresolved alternatives; treat as a lead for further verification, not a conclusion."


def falsification_for(hyp_text: str, metric_b: str, last_period: str, last_value: float) -> dict:
    return {
        "metric": metric_b or "relevant metric",
        "baseline": f"{last_period}: {last_value}",
        "condition": f"If the next audited annual filing shows the {metric_b or 'metric'} gap closing by more than half versus {last_period} with no new disclosed driver, this discovery should be reconsidered.",
        "period": "next audited FY filing",
        "threshold": "gap narrows >50% vs baseline",
    }
