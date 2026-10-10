# SIGNAL HUNTER X — Autonomous Financial Intelligence & Hidden Signal Discovery

> “Don't summarize the market. Discover what it's missing.”
> “Every signal has a story. Every story needs evidence.”

Institutional-quality autonomous financial investigation for Indian listed companies (NSE/BSE, INR, Indian FY conventions). ATMOS 2026 · BITS Pilani, Hyderabad Campus.

**Research tool — not investment advice. No buy/sell recommendations. Never fabricate: insufficient evidence returns an honest “Insufficient evidence for a defensible discovery”.**

---

## 1. Quickstart (local, no keys required)

Prerequisites: Python 3.11+, Node 20+.

```bash
# Backend (works with zero API keys: built-in search + deterministic engine)
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000        # → http://localhost:8000/api/health

# Frontend (new terminal)
cd frontend
npm install
npm run dev                                       # → http://localhost:3000
```

Optional upgrades via `backend/.env` (all graceful — system works without them):

| Variable | Effect |
|---|---|
| `SEARCH_PROVIDER=serper` + `SERPER_API_KEY` | Higher-recall web search (default `builtin` = keyless DuckDuckGo) |
| `SEARCH_PROVIDER=tavily` + `TAVILY_API_KEY` | Same via Tavily |
| `LLM_PROVIDER=openai_compatible` + `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL` | LLM explanations (calculations stay deterministic regardless) |
| `DATABASE_URL=postgresql+psycopg2://…` | Postgres instead of SQLite (needs `psycopg2-binary`) |
| `REDIS_URL=…` | Reserved for Redis-backed jobs (default: in-process asyncio) |

Docker:

```bash
docker compose up --build   # frontend :3000, backend :8000
```

Demo fixture (clearly labeled fictional layout demo, never live research):

```bash
cd backend && python -m app.seed_demo
```

## 2. How it works

Eleven persisted stages, executed in order by `backend/app/engine/pipeline.py`:

`resolve → plan → discover → extract → financials → patterns → hypothesize → triangulate → adversarial → assess → report`

- **Resolve**: ticker/exchange/sector/IR site from a 40-company registry (Tracks A–D); ambiguous input rejected with suggestions.
- **Plan**: 3 track-specific candidate questions with disprove tests + priority scores (novelty/materiality/evidence/testability).
- **Discover**: public search (filings, annual reports, results, presentations, transcripts, press, peers) + official IR/exchange seeds. URL, publisher, timestamps, doc type, content hash stored.
- **Extract**: SSRF-guarded fetch (timeout, byte cap, 1 req/s politeness, retries), trafilatura/BeautifulSoup HTML, PyMuPDF PDFs, verbatim financial passages only.
- **Financials**: Screener.in public annuals parsed generically + `finlib-v1` deterministic normalization (₹/lakh/crore, FY Apr–Mar, standalone vs consolidated tags, YoY/margins/CAGR, NaN propagation — never imputation).
- **Patterns**: divergence (|growth gap| > 15pp or opposing slopes), working-capital divergence, margin swings (>3pp), pct-change z-score anomalies.
- **Hypothesize / Triangulate / Adversarial**: competing explanations, peer-leg comparison, dedicated contrary-evidence search, steel-man alternative with ruled_out/unresolved verdict.
- **Assess**: Strong needs ≥3 independent publisher lines + reproducible calcs + tested counterargument; else Moderate/Weak.
- **Report**: flagship page A–J (overview, why-it-matters, key numbers, charts, timeline, evidence trail, counterargument, falsification, strength, sources/methodology) + print-to-PDF export.

## 3. API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/research` | `{company, exchange, track, period, depth}` → `{id}` |
| GET | `/api/research/{id}` | status, stage, events, plan, patterns |
| GET | `/api/research/{id}/events` | SSE stream + polling fallback |
| POST | `/api/research/{id}/cancel` | cancel running job |
| POST | `/api/research/{id}/retry` | retry failed/cancelled (409 otherwise) |
| GET | `/api/discoveries/{id}` | full discovery |
| GET | `/api/discoveries/{id}/evidence` | sources → passages, metrics + formulas, hypotheses |
| GET | `/api/discoveries/{id}/export` | print-ready HTML report |
| GET | `/api/history?search&track&status&limit&offset` | past investigations |
| GET | `/api/companies/search?q=` | registry suggestions |
| GET | `/api/health` · `/api/config` | health + provider status |

## 4. Testing

```bash
cd backend && python -m pytest tests/ -q
```

Covers: INR/fiscal normalization, YoY/margin/CAGR + NaN policy, anomaly z-scores, peer ranks, dedup, company resolution, plan scoring, adversarial/strength rules, claim-verbatim validation, Screener fixture parse, API validation + state transitions (incl. 409 on illegal retry). Live-source runs are manual: launch any ticker at `/research/new` and inspect the evidence trail.

## 5. Project layout

```
backend/app/{main,config,db,models,schemas}.py
backend/app/api/routes.py            # REST surface
backend/app/engine/{pipeline,jobs}.py# staged orchestrator + job runner
backend/app/services/               # ssrf, search, fetcher, screener, finance,
                                     # planner, analysis, llm, companies, exporter
backend/tests/                       # pytest suite
frontend/app/                        # /, research/new, research/[id], discoveries/[id],
                                     # history, methodology, settings
frontend/components/ frontend/lib/
```

## 6. Security & reliability

Server-side keys only · input validation (Pydantic + query guards) · SSRF allowlist-style guard (public IPs blocked, redirect-capped) · fetch timeouts + 6 MB cap + politeness delay · output is quoted passages + computed numbers (retrieved content never executed) · structured logs · `/api/health` · cancel/retry on every job.
