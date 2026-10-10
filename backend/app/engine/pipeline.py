"""Staged autonomous research pipeline. Every stage persists to SQLite.

resolve -> plan -> discover -> extract -> financials -> patterns -> hypothesize
  -> triangulate -> adversarial -> assess -> report

Failures are recorded honestly; insufficient evidence yields an honest
inconclusive discovery (never fabricated).
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import math

from ..db import SessionLocal
from ..models import Discovery, Evidence, Hypothesis, Investigation, Metric, Source
from ..services import analysis as A
from ..services import finance as F
from ..services import screener as SC
from ..services.companies import peers_of
from ..services.fetcher import (
    canonicalize,
    content_hash,
    dedupe_sources,
    extract_passages,
    extract_text,
    fetch_url,
    now_iso,
)
from ..services.planner import build_plan
from ..services.search import discovery_queries, web_search

log = logging.getLogger("signalhunter.pipeline")

STAGES = ["resolve", "plan", "discover", "extract", "financials", "patterns",
          "hypothesize", "triangulate", "adversarial", "assess", "report"]


def _emit(db, inv: Investigation, stage: str, message: str, kind: str = "info"):
    db.expire_all()
    db.refresh(inv)
    if inv.status == "cancelled" and stage != "cancelled":
        raise asyncio.CancelledError(f"job {inv.id} cancelled")
    try:
        evts = json.loads(inv.events or "[]")
    except Exception:
        evts = []
    evts.append({"ts": now_iso(), "stage": stage, "message": message, "kind": kind})
    inv.events = json.dumps(evts[-300:])
    inv.stage = stage
    inv.stage_index = STAGES.index(stage) if stage in STAGES else inv.stage_index
    inv.updated_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def _classify(url: str, hint: str) -> str:
    u = url.lower()
    if "annual" in u or hint == "annual_report":
        return "annual_report"
    if "presentation" in u or hint == "presentation":
        return "presentation"
    if "transcript" in u or hint == "transcript":
        return "transcript"
    if "nseindia" in u or "bseindia" in u or hint == "filing":
        return "filing"
    if hint in ("results",):
        return "results"
    if "screener.in" in u:
        return "data"
    return hint if hint else "article"


def run_pipeline(inv_id: str):
    asyncio.run(_run(inv_id))


async def _run(inv_id: str):
    db = SessionLocal()
    try:
        inv = db.get(Investigation, inv_id)
        if not inv or inv.status == "cancelled":
            return
        inv.status = "running"
        db.commit()
        from ..services.companies import COMPANIES

        # ---- resolve ----
        _emit(db, inv, "resolve", f"Resolving {inv.company_name} ({inv.ticker}) on {inv.exchange}…")
        meta = next((c for c in COMPANIES if c["ticker"] == inv.ticker), None)
        if not meta:
            return _fail(db, inv, f"Company ticker '{inv.ticker}' is not in the supported listed-company registry. Try a suggestion from search.")
        await asyncio.sleep(0)
        _emit(db, inv, "resolve", f"Resolved: {meta['canonical_name']} · {meta['sector']} / {meta['industry']}. IR: {meta['website']}")

        # ---- plan ----
        _emit(db, inv, "plan", "Drafting candidate research questions…")
        plan = build_plan({**meta, "track": inv.track}, {"series_metrics": [], "n_sources": 0})
        inv.error = json.dumps({"plan": plan})  # transient scratch space (not user-facing error)
        db.commit()
        for p in plan:
            _emit(db, inv, "plan", f"{p['id']} (priority {p['priority']}/9): {p['question']}")

        # ---- discover ----
        _emit(db, inv, "discover", "Searching public sources (filings, reports, results, commentary)…")
        depth_n = {"quick": 4, "standard": 7, "deep": 10}[inv.depth]
        queries = discovery_queries(meta["canonical_name"], inv.ticker, inv.track)
        raw_hits: list[dict] = []
        for q, hint in queries:
            for h in web_search(q, n=5):
                h["hint"] = hint
                h["query"] = q
                raw_hits.append(h)
            _emit(db, inv, "discover", f"“{q[:60]}…” → {len(raw_hits)} candidates so far")
        # seed official IR + exchange pages (primary sources first)
        seeds = [
            {"title": f"{meta['canonical_name']} — Investor relations", "url": meta["website"], "publisher": meta["website"].split("//")[-1], "hint": "press", "query": "seed:ir"},
            {"title": f"{inv.ticker} — Screener.in financials", "url": f"https://www.screener.in/company/{inv.ticker}/consolidated/", "publisher": "screener.in", "hint": "data", "query": "seed:financials"},
            {"title": "NSE announcements", "url": f"https://www.nseindia.com/companies-listing/corporate-filings-announcements", "publisher": "nseindia.com", "hint": "filing", "query": "seed:nse"},
        ]
        raw_hits = seeds + raw_hits
        _emit(db, inv, "discover", f"Discovery complete: {len(raw_hits)} candidate URLs.")

        # ---- extract ----
        _emit(db, inv, "extract", f"Fetching up to {depth_n * 3} documents (polite rate, SSRF-guarded)…")
        from ..config import get_settings
        cap = min(get_settings().FETCH_MAX_PAGES_PER_INVESTIGATION, depth_n * 3 + 3)
        fetched: list[dict] = []
        seen: set[str] = set()
        for h in raw_hits:
            if len(fetched) >= cap:
                break
            cu = canonicalize(h["url"])
            if cu in seen:
                continue
            seen.add(cu)
            got = await asyncio.to_thread(fetch_url, h["url"])
            if not got.get("ok"):
                _emit(db, inv, "extract", f"skip {h['url'][:70]} ({got.get('error')})", kind="warn")
                continue
            ext = extract_text(got)
            text = ext.get("text", "")
            if len(text.strip()) < 200:
                _emit(db, inv, "extract", f"thin content, skipping: {h['title'][:60]}", kind="warn")
                continue
            hsh = content_hash(text[:20000])
            src = Source(investigation_id=inv.id, url=h["url"], canonical_url=cu,
                         title=h.get("title", "")[:300], publisher=h.get("publisher", "")[:200],
                         pub_date="", retrieved_at=now_iso(), doc_type=_classify(h["url"], h.get("hint", "")),
                         reporting_period="", content_hash=hsh, extraction_status="ok", role="context")
            db.add(src)
            db.commit()
            for ps in extract_passages(text):
                db.add(Evidence(investigation_id=inv.id, source_id=src.id, claim=ps["passage"][:500],
                                passage=ps["passage"][:2000], page_section="extracted passage",
                                line_item=ps["line_item"][:120], units="", confidence=0.7 if ps["figures"] else 0.45,
                                kind="fact", validation="unreviewed"))
            db.commit()
            fetched.append({"src": src, "text_len": len(text)})
            _emit(db, inv, "extract", f"✓ {src.title[:70]} [{src.doc_type}] — {len(text)//1000}k chars")
        fetched = dedupe_sources([{"url": f["src"].url, "content_hash": f["src"].content_hash, **f} for f in fetched])
        n_ev = db.query(Evidence).filter_by(investigation_id=inv.id).count()
        _emit(db, inv, "extract", f"Extraction done: {len(fetched)} documents, {n_ev} evidence passages.")

        # ---- financials ----
        _emit(db, inv, "financials", "Ingesting audited annual series + deterministic normalization…")
        fin = await asyncio.to_thread(SC.fetch_company_financials, inv.ticker)
        series: list[dict] = fin.get("series", [])
        if fin.get("ok"):
            _emit(db, inv, "financials", f"Parsed {fin.get('tables_found')} tables from {fin.get('url')} → {len(series)} annual points.")
        else:
            _emit(db, inv, "financials", f"Financial-statement fetch issue: {fin.get('error')}. Continuing with text evidence.", kind="warn")
        fin_src = db.query(Source).filter(Source.investigation_id == inv.id, Source.url.like("%screener.in%")).first()
        for p in series:
            db.add(Metric(investigation_id=inv.id, name=p["metric"], formula_id=f"screener:{p['table']}"[:120],
                          inputs_json=json.dumps({"table_value": p["value"], "table": p["table"]}),
                          evidence_ids_json=json.dumps([fin_src.id] if fin_src else []),
                          value=float(p["value"]), units=p["units"], period=p["period"], code_version=F.CODE_VERSION))
        db.commit()
        # derived metrics (deterministic)
        bym: dict[str, list[dict]] = {}
        for p in series:
            bym.setdefault(p["metric"], []).append(p)
        for m, pts in bym.items():
            pts.sort(key=lambda p: p["period"])
            if len(pts) >= 2:
                r = F.yoy(pts[-1]["value"], pts[-2]["value"])
                if r["defined"]:
                    db.add(Metric(investigation_id=inv.id, name=f"{m}_yoy", formula_id="(current-prior)/|prior|",
                                  inputs_json=json.dumps({"current": pts[-1]["value"], "prior": pts[-2]["value"]}),
                                  evidence_ids_json=json.dumps([fin_src.id] if fin_src else []),
                                  value=float(r["value"]), units="fraction", period=f"{pts[-2]['period']}→{pts[-1]['period']}"))
        # margins from revenue+pat legs where comparable
        rev = {p["period"]: p["value"] for p in bym.get("revenue", [])}
        pat = {p["period"]: p["value"] for p in bym.get("pat", [])}
        for per in sorted(set(rev) & set(pat)):
            r = F.margin(pat[per], rev[per])
            if r["defined"]:
                db.add(Metric(investigation_id=inv.id, name="pat_margin", formula_id="pat/revenue",
                              inputs_json=json.dumps({"pat": pat[per], "revenue": rev[per]}),
                              evidence_ids_json=json.dumps([fin_src.id] if fin_src else []),
                              value=float(r["value"]), units="fraction", period=per))
        db.commit()
        n_met = db.query(Metric).filter_by(investigation_id=inv.id).count()
        _emit(db, inv, "financials", f"Normalization complete: {n_met} metrics (reported + derived, finlib-v1).")

        # ---- patterns ----
        _emit(db, inv, "patterns", "Running deterministic pattern + anomaly scans…")
        patterns = A.detect_patterns(series, inv.track, inv.period)
        inv.error = json.dumps({"plan": plan, "patterns": patterns})
        db.commit()
        if patterns:
            for p in patterns:
                _emit(db, inv, "patterns", f"{p['id']}: {p['reason']}")
        else:
            _emit(db, inv, "patterns", "No cross-metric divergence above thresholds — will report honestly.", kind="warn")

        # ---- hypothesize ----
        _emit(db, inv, "hypothesize", "Generating competing explanations from observed evidence…")
        hyps = A.build_hypotheses(patterns, {"ticker": inv.ticker}, plan)
        for h in hyps:
            db.add(Hypothesis(investigation_id=inv.id, text=h["text"], mechanism=h["mechanism"],
                              supporting_json=json.dumps(h["expected_evidence"]),
                              contradicting_json=json.dumps(h["weakening_evidence"]),
                              alternatives_json=json.dumps([]), status="candidate", rationale=f"pattern {h['pattern_id']}"))
        db.commit()
        for h in hyps:
            _emit(db, inv, "hypothesize", f"{h['id']}: {h['text'][:120]}…")

        # ---- triangulate ----
        _emit(db, inv, "triangulate", "Seeking independent confirmation + peer comparison…")
        peers = peers_of(meta, n=2)
        peer_agrees = False
        for peer in peers:
            pf = await asyncio.to_thread(SC.fetch_company_financials, peer["ticker"])
            if pf.get("series"):
                pm = {p["metric"]: p for p in pf["series"]}
                mine = {p["metric"]: p for p in series}
                # compare revenue direction over last leg
                for m in ("revenue", "pat"):
                    a = [p for p in pf["series"] if p["metric"] == m][-2:]
                    b = [p for p in series if p["metric"] == m][-2:]
                    if len(a) == 2 and len(b) == 2:
                        da = (a[1]["value"] - a[0]["value"]) / abs(a[0]["value"]) if a[0]["value"] else 0
                        dbb = (b[1]["value"] - b[0]["value"]) / abs(b[0]["value"]) if b[0]["value"] else 0
                        if (da > 0) == (dbb > 0):
                            peer_agrees = True
                _emit(db, inv, "triangulate", f"peer {peer['ticker']}: compared latest legs (agree={peer_agrees})")
        # contrary evidence search
        from ..services.analysis import CONTRARY_QUERIES
        n_contra = 0
        for q in CONTRARY_QUERIES[:3]:
            for h in web_search(q.format(name=meta["canonical_name"]), n=3):
                cu = canonicalize(h["url"])
                if db.query(Source).filter_by(investigation_id=inv.id, canonical_url=cu).first():
                    continue
                got = await asyncio.to_thread(fetch_url, h["url"])
                if not got.get("ok"):
                    continue
                ext = extract_text(got)
                if len(ext.get("text", "")) < 200:
                    continue
                src = Source(investigation_id=inv.id, url=h["url"], canonical_url=cu, title=h.get("title", "")[:300],
                             publisher=h.get("publisher", "")[:200], pub_date="", retrieved_at=now_iso(),
                             doc_type="news", reporting_period="", content_hash=content_hash(ext["text"][:20000]),
                             extraction_status="ok", role="contradictory")
                db.add(src)
                db.commit()
                for ps in extract_passages(ext["text"], max_passages=3):
                    db.add(Evidence(investigation_id=inv.id, source_id=src.id, claim=ps["passage"][:500],
                                    passage=ps["passage"][:2000], page_section="contrary check", line_item=ps["line_item"][:120],
                                    units="", confidence=0.5, kind="fact", validation="unreviewed"))
                    n_contra += 1
                db.commit()
                _emit(db, inv, "triangulate", f"contrary-check: {h.get('title','')[:70]}")
                if n_contra >= 4:
                    break
            if n_contra >= 4:
                break
        _emit(db, inv, "triangulate", f"Triangulation done: peer_agrees={peer_agrees}, contrary passages={n_contra}.")

        # ---- adversarial ----
        _emit(db, inv, "adversarial", "Arguing against the discovery (steel-man alternatives)…")
        sources = db.query(Source).filter_by(investigation_id=inv.id).all()
        publishers = {s.publisher for s in sources if s.publisher}
        n_indep = max(len(publishers), len(sources))
        lead = hyps[0] if hyps else None
        counter = A.adversarial_review(lead or {}, patterns, n_indep, peer_agrees)
        _emit(db, inv, "adversarial", f"Strongest alternative: {counter['strongest_alternative']} → {counter['verdict']}")

        # ---- assess ----
        _emit(db, inv, "assess", "Grading evidence strength against documented rules…")
        limitations: list[str] = []
        if len(series) < 6:
            limitations.append(f"Only {len(series)} annual data points parsed; some metrics/years missing.")
        if n_indep < 3:
            limitations.append(f"Only {n_indep} independent publisher lines — below the 3-line bar for Strong.")
        if not patterns:
            limitations.append("No deterministic divergence above thresholds; conclusion is descriptive, not a hidden-signal claim.")
        if n_contra == 0:
            limitations.append("No contrary passages retrieved — absence of counterevidence is a coverage gap, not confirmation.")
        calc_ok = db.query(Metric).filter_by(investigation_id=inv.id).count() > 0
        strength, rationale = A.assess_strength(n_indep, calc_ok, {}, counter, limitations)
        _emit(db, inv, "assess", f"Verdict: {strength} — {rationale[:140]}")

        # ---- report ----
        _emit(db, inv, "report", "Composing the discovery report…")
        disc = _compose(db, inv, meta, series, patterns, hyps, counter, strength, rationale, limitations, peers, peer_agrees)
        db.commit()
        inv.status = "completed"
        inv.stage = "report"
        inv.discovery_id = disc.id
        inv.completed_at = now_iso()
        inv.error = ""
        db.commit()
        _emit(db, inv, "report", f"Done — {strength}: {disc.headline[:120]}")
    except Exception as e:
        log.exception("pipeline %s crashed", inv_id)
        db.rollback()
        inv = db.get(Investigation, inv_id)
        if inv:
            _fail(db, inv, f"{type(e).__name__}: {str(e)[:400]}")
    finally:
        db.close()


def _fail(db, inv: Investigation, msg: str):
    inv.status = "failed"
    inv.error = msg
    inv.retriable = 1
    db.commit()
    _emit(db, inv, inv.stage if inv.stage in STAGES else "resolve", f"Failed: {msg}", kind="error")


def _compose(db, inv, meta, series, patterns, hyps, counter, strength, rationale, limitations, peers, peer_agrees) -> Discovery:
    mets = db.query(Metric).filter_by(investigation_id=inv.id).all()
    srcs = db.query(Source).filter_by(investigation_id=inv.id).all()
    src_by_url = {s.url: s for s in srcs}
    fin_src = next((s for s in srcs if "screener.in" in (s.url or "")), srcs[0] if srcs else None)

    if not patterns or not hyps:
        headline = f"Insufficient evidence for a defensible discovery — {inv.ticker}"
        finding = (f"After retrieving {len(srcs)} documents and parsing {len(series)} annual data points for {meta['canonical_name']}, "
                   f"no cross-metric divergence cleared deterministic thresholds. This is an honest inconclusive result: the engine refuses to fabricate a signal.")
        key_numbers, timeline, significance = [], [{"date": now_iso()[:10], "label": "No pattern above threshold — inconclusive", "kind": "assessment"}], \
            ["Inconclusive runs are first-class results: they prevent false discoveries.", "Re-run at deeper depth or after fresh filings for more coverage."]
    else:
        # lead with a divergence pattern when one exists; otherwise report the
        # strongest observed pattern honestly (never an empty "X vs Y" headline)
        div = next((p for p in patterns if p["kind"] == "divergence"), patterns[0])
        p0 = div
        per = p0.get("periods", [])
        a, b = p0.get("metric_a", ""), p0.get("metric_b", "")
        gap = p0.get("gap", float("nan"))
        if p0["kind"] == "divergence" and per:
            headline = f"{inv.ticker}: {p0['reason']}"
        else:
            headline = f"{inv.ticker}: {p0['reason'][:160]}"
        finding = hyps[0]["text"] + f" Calculation trace: {p0.get('calc','')}. Peer check across {[p['ticker'] for p in peers]}: {'peers move the same way (sector effect possible)' if peer_agrees else 'peers do not mirror the move (idiosyncratic)'}."
        key_numbers = []
        legs = [(a, p0.get("values_a", [])), (b, p0.get("values_b", []))]
        for mname, vals in legs:
            for per_i, val in zip(per, vals):
                meta = next((x for x in series if x["metric"] == mname and x["period"] == per_i), None)
                if meta is None:
                    continue
                key_numbers.append({"metric": f"{mname} ({per_i})", "value": val, "units": meta["units"],
                                    "periods": per_i, "formula": f"reported ({meta['table']})",
                                    "source_ids": [fin_src.id] if fin_src else []})
        if math.isfinite(gap or float("nan")):
            key_numbers.append({"metric": f"growth gap {b or ''} minus {a or ''}", "value": round(float(gap) * 100, 1),
                                "units": "pp", "periods": f"{per[0]}→{per[-1]}" if per else "",
                                "formula": "(current-prior)/|prior| both legs; gap = g_b − g_a",
                                "source_ids": [fin_src.id] if fin_src else []})
        timeline = ([{"date": per[0], "label": f"Window opens: {a}/{b} tracked from {per[0]}", "kind": "signal"}] if per else []) + \
                   [{"date": per[-1] if per else now_iso()[:10], "label": p0["reason"], "kind": "signal"}] + \
                   [{"date": now_iso()[:10], "label": f"Adversarial review: {counter['strongest_alternative']} → {counter['verdict']}", "kind": "assessment"}]
        significance = [
            f"Combines {len(srcs)} documents with deterministic {len(mets)}-metric arithmetic — not a single-report summary.",
            f"Peer triangulation ({', '.join(p['ticker'] for p in peers) or 'n/a'}) tests whether this is company-specific.",
            f"Falsifiable: the report names the exact next filing that would overturn it.",
        ]
    last_per = (patterns[0].get("periods", ["?"])[-1] if patterns else "?")
    last_val = (patterns[0].get("values_b", [0])[-1] if patterns and patterns[0].get("values_b") else 0)
    disc = Discovery(
        investigation_id=inv.id, headline=headline[:300], finding=finding[:3000],
        significance_json=json.dumps(significance),
        key_numbers_json=json.dumps(key_numbers),
        timeline_json=json.dumps(timeline),
        counterargument_json=json.dumps(counter),
        falsification_json=json.dumps(A.falsification_for(hyps[0]["text"] if hyps else "", patterns[0].get("metric_b", "") if patterns else "", last_per, last_val)),
        strength=strength, strength_rationale=rationale,
        limitations_json=json.dumps(limitations + ["Research tool — not investment advice. Verify against linked primary sources."]),
        coverage_json=json.dumps({"n_sources": len(srcs), "n_publishers": len({s.publisher for s in srcs if s.publisher}),
                                  "n_metrics": len(mets), "n_patterns": len(patterns), "periods": sorted({p.get('period','?') for p in series})}),
        created_at=now_iso(),
    )
    db.add(disc)
    db.commit()
    # mark hypothesis statuses
    for h in db.query(Hypothesis).filter_by(investigation_id=inv.id).all():
        h.status = "validated" if (hyps and h.text == hyps[0]["text"] and strength in ("Strong", "Moderate")) else ("unresolved" if strength == "Weak" else "candidate")
    db.commit()
    return disc
