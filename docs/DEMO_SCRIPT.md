# SIGNAL HUNTER X — Demo Script

## 2-minute MVP demo
1. **Home** (`/`): “Find the financial story hiding in plain sight.” Point at the 5-capability strip and the 6-step loop (Investigate→…→Prove). *(10s)*
2. **New Investigation** (`/research/new`): type a ticker (e.g. `ITC`), pick Track C, quick depth, **Start research**. *(15s)*
3. **Live workspace** (`/research/[id]`): show the stage chips advancing and the **live evidence stream** — real documents being fetched (transcripts, presentations, filings). Stress: *no fake percentages; only backend-reported states.* *(35s)*
4. **Discovery report** (`/discoveries/[id]`): 
   - Headline + strength badge + coverage (sources/metrics). 
   - **Key numbers** table → click a source link → the real document opens. 
   - **Evidence trail** → expand a source → show the **verbatim passage**. 
   - **Counterargument** (the alternative we tried to falsify) + **Falsification condition**. *(45s)*
5. **Print/PDF** export. *(10s)*
6. Close: “Same pipeline, any company, no company-specific tuning. And when evidence is thin, it says so.” *(5s)*

## 10-minute final presentation
1. **Problem & wedge** (1 min): dashboards summarize; we *discover and defend*.
2. **Live run on an unfamiliar company** (3 min): launch a ticker not used in development; narrate the stages as they stream.
3. **Anatomy of the discovery** (2.5 min): walk A→J; dwell on **F Evidence trail** (verbatim passage + document), **G Counterargument**, **H Falsification**, **I Strength** (the rules).
4. **Determinism & provenance** (1.5 min): open **J** → show `finlib-v1` formula + inputs per metric; explain why the LLM never computes.
5. **Robustness** (1 min): show a **failed / insufficient** run and how it reports honestly; show cancel/retry.
6. **Generality** (1 min): four tracks, 40 companies, no company-specific code; swap providers via env.

## Judge Q&A cheat-sheet
- *“Where do numbers come from?”* Public financials pages + filings, parsed deterministically; each metric stores formula, inputs, evidence IDs, code version.
- *“How do you avoid fabricating?”* Verbatim-only passages; below-threshold → “insufficient evidence”; failures recorded, never dressed up as success.
- *“Independence?”* Publisher + content-hash dedup; repeated coverage of one announcement counts once.
- *“Novelty?”* Cross-metric divergence + peer beta test + contrary sweep, which no single report surfaces together.
- *“Falsifiable?”* Every discovery names the next filing/metric/threshold that would overturn it.
