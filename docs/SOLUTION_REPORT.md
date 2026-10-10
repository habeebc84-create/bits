# SIGNAL HUNTER X — Round 1 Solution Report

## Problem
Conventional dashboards and single-report summarizers describe what already happened. They do not *connect* filings, results, commentary, peers, and time into a defensible, verifiable discovery — and they rarely argue against their own conclusion.

## Solution
**SIGNAL HUNTER X** is an autonomous research agent that investigates any eligible Indian listed company and returns a *falsifiable, fully-cited* discovery — or an honest “insufficient evidence” result. It never fabricates numbers, quotes, or links.

## Architecture
```
Next.js 15 (App Router, TS, Tailwind)  ──  FastAPI (Python)  ──  SQLite/Postgres
        │                                        │
        │  poll + SSE                            ├─ engine/pipeline.py  (11 persisted stages)
        └───────────────────────────────────►    ├─ engine/jobs.py      (async worker)
                                                 └─ services/  ssrf · search · fetcher · screener
                                                                 finance(finlib-v1) · planner · analysis
                                                                 llm(optional) · companies · exporter
```

## The research workflow (all persisted, all real)
1. **Resolve** — canonical name/ticker/exchange/sector/IR from a 40-name registry; ambiguous input rejected with suggestions.
2. **Plan** — 3 track-specific questions, each with hypothesis, why-it-matters, required evidence, alternative, **disprove test**, and a priority score.
3. **Discover** — public search across filings/annual reports/results/presentations/transcripts/press + official IR & exchange seeds. URL, publisher, timestamps, doc type, content hash stored.
4. **Extract** — SSRF-guarded fetch (timeout, byte cap, 1 req/s politeness), trafilatura/bs4 HTML, PyMuPDF PDFs; **verbatim** financial passages only.
5. **Financials** — Screener.in public annuals parsed generically (annual-only, standalone/consolidated tagged, deduped) + `finlib-v1` normalization (₹/lakh/crore, FY Apr–Mar, YoY/margins/CAGR, NaN propagation — never imputation).
6. **Patterns** — divergence (opposing slopes or >15pp growth gap), working-capital divergence, margin swings (>3pp), pct-change z-score anomalies, all within the requested period window.
7. **Hypothesize** — competing explanations with mechanism, expected/weakening evidence.
8. **Triangulate** — peer-leg comparison + a dedicated contrary-evidence search.
9. **Adversarial** — steel-mans the strongest alternative (one-off/restatement, sector-wide beta, seasonality, thin evidence) with a ruled-out / unresolved verdict.
10. **Assess** — strength grading where **Strong** requires ≥3 independent lines + reproducible calcs + a *ruled-out* strongest alternative; an unresolved alternative caps at **Moderate**.
11. **Report** — the flagship A–J dashboard + print-to-PDF export.

## Why it is defensible (and not a summarizer)
- **Deterministic calculations**: the LLM is never the calculator of record; every metric stores formula, inputs, evidence refs, and code version (`finlib-v1`).
- **Independent triangulation**: repeated coverage of one announcement is not counted as independent confirmation (publisher + content-hash dedup).
- **Adversarial by construction**: a dedicated stage tries to *falsify* the finding before grading it.
- **Falsifiable output**: every discovery names the exact future filing/metric/threshold that would overturn it.
- **Honesty**: below-threshold runs return “Insufficient evidence for a defensible discovery” with the coverage gap explained.

## Evidence trail
Discovery → claims → metrics (formula + inputs) → documents → **verbatim passages** → counterclaims → alternatives. Every number on the report links to its source document; clicking a claim reveals the passage, line item, page/section, confidence, and external link.

## Configuration & grace
Works with **zero API keys** (keyless search + deterministic engine). Optional `SEARCH_PROVIDER=serper|tavily` and `LLM_PROVIDER=openai_compatible` upgrade recall/narrative; calculations stay deterministic regardless.

## Testing
15 automated tests (pytest): INR/unit parsing, fiscal normalization & comparability, YoY/margin/CAGR + NaN policy, anomaly z-scores, peer ranks, source dedup, company resolution, plan scoring, **direction-aware divergence + period window**, adversarial + strength caps, verbatim-claim validation, Screener fixture parse, and a **hermetic end-to-end pipeline** (resolve→report) plus API validation & job state transitions. Live-source runs are manual and documented as such.

## Limitations (stated, not hidden)
Public sources only; parser depends on public financials pages; LLM optional. Missing/unparseable data is surfaced as a limitation, never imputed.

## What makes a judge say “I could not have found this in one report”
The engine combines an audited multi-year series, a cross-metric divergence within a chosen window, peer movement (sector-beta test), and a contrary-evidence sweep — then explicitly states the single filing that would prove it wrong. That chain is reproducible, clickable, and honest.
