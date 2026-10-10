"""REST API per spec + company search + config status. Typed, validated, safe errors."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from ..db import SessionLocal
from ..engine import jobs
from ..engine.pipeline import STAGES, run_pipeline
from ..models import Discovery, Evidence, Hypothesis, Investigation, Metric, Source
from ..schemas import ResearchCreate
from ..services import llm
from ..services.companies import COMPANIES, resolve_company, search_companies
from ..services.exporter import render_html
from ..services.fetcher import now_iso

router = APIRouter()


def _db():
    return SessionLocal()


def _inv_dict(inv: Investigation) -> dict:
    try:
        events = json.loads(inv.events or "[]")
    except Exception:
        events = []
    return {"id": inv.id, "company_name": inv.company_name, "ticker": inv.ticker,
            "exchange": inv.exchange, "track": inv.track, "period": inv.period, "depth": inv.depth,
            "status": inv.status, "stage": inv.stage, "stage_index": inv.stage_index,
            "stages": STAGES, "error": inv.error if inv.status in ("failed",) else "",
            "discovery_id": inv.discovery_id, "created_at": inv.created_at.isoformat() if inv.created_at else "",
            "completed_at": inv.completed_at, "n_events": len(events)}


@router.get("/health")
def health():
    from ..config import get_settings
    s = get_settings()
    return {"ok": True, "env": s.APP_ENV, "llm": llm.status(),
            "search": {"provider": s.SEARCH_PROVIDER,
                       "configured": True if s.SEARCH_PROVIDER == "builtin" else bool(s.SERPER_API_KEY or s.TAVILY_API_KEY)}}


@router.get("/config")
def config():
    from ..config import get_settings
    s = get_settings()
    return {"llm": llm.status(),
            "search": {"provider": s.SEARCH_PROVIDER,
                       "configured": True if s.SEARCH_PROVIDER == "builtin" else bool(s.SERPER_API_KEY or s.TAVILY_API_KEY)},
            "fetch": {"timeout_s": s.FETCH_TIMEOUT_S, "max_pages": s.FETCH_MAX_PAGES_PER_INVESTIGATION},
            "tracks": {"A": "Banking, NBFCs & Financial Services", "B": "Energy, Power & Renewables",
                       "C": "Consumer, FMCG & Retail", "D": "Pharma & Healthcare"}}


@router.get("/companies/search")
def companies_search(q: str = Query(min_length=1, max_length=64), limit: int = 8):
    return {"results": search_companies(q, limit)}


@router.post("/research", status_code=201)
def create_research(body: ResearchCreate):
    meta = resolve_company(body.company, body.exchange)
    if not meta:
        raise HTTPException(400, f"Could not resolve '{body.company}' to a supported NSE/BSE listed company. Use /api/companies/search for suggestions.")
    db = _db()
    try:
        # reuse canonical company row or create
        from ..models import Company
        comp = db.query(Company).filter_by(ticker=meta["ticker"]).first()
        if not comp:
            comp = Company(canonical_name=meta["canonical_name"], ticker=meta["ticker"],
                           exchange=body.exchange, sector=meta["sector"], industry=meta["industry"], website=meta["website"])
            db.add(comp)
            db.commit()
        inv = Investigation(company_id=comp.id, company_name=meta["canonical_name"], ticker=meta["ticker"],
                            exchange=body.exchange, track=body.track, period=body.period, depth=body.depth,
                            status="queued", stage="queued")
        db.add(inv)
        db.commit()
        inv_id = inv.id
    finally:
        db.close()
    jobs.submit(inv_id, lambda: run_pipeline(inv_id))
    return {"id": inv_id}


@router.get("/research/{rid}")
def get_research(rid: str):
    db = _db()
    try:
        inv = db.get(Investigation, rid)
        if not inv:
            raise HTTPException(404, "investigation not found")
        d = _inv_dict(inv)
        try:
            d["events"] = json.loads(inv.events or "[]")[-60:]
        except Exception:
            d["events"] = []
        # research plan panel (persisted in pipeline scratch)
        try:
            scratch = json.loads(inv.error or "{}") if inv.status not in ("failed",) else {}
            d["plan"] = scratch.get("plan", [])
            d["patterns"] = scratch.get("patterns", [])
        except Exception:
            d["plan"] = []
            d["patterns"] = []
        return d
    finally:
        db.close()


@router.get("/research/{rid}/events")
async def research_events(rid: str):
    import asyncio

    async def gen():
        db = SessionLocal()
        try:
            inv = db.get(Investigation, rid)
            if not inv:
                yield 'event: error\ndata: {"message": "not found"}\n\n'
                return
            try:
                seen = len(json.loads(inv.events or "[]"))
            except Exception:
                seen = 0
            yield f"event: stage\ndata: {json.dumps({'stage': inv.stage, 'status': inv.status})}\n\n"
            for _ in range(600):  # ~20 min max stream
                await asyncio.sleep(2)
                db.expire_all()
                inv = db.get(Investigation, rid)
                if not inv:
                    break
                try:
                    evts = json.loads(inv.events or "[]")
                except Exception:
                    evts = []
                for e in evts[seen:]:
                    yield f"event: event\ndata: {json.dumps(e)}\n\n"
                seen = len(evts)
                if inv.status in ("completed", "failed", "cancelled"):
                    yield f"event: done\ndata: {json.dumps({'status': inv.status, 'discovery_id': inv.discovery_id})}\n\n"
                    break
        finally:
            db.close()

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/research/{rid}/cancel")
def cancel_research(rid: str):
    stopped = jobs.cancel(rid)
    db = _db()
    try:
        inv = db.get(Investigation, rid)
        if not inv:
            raise HTTPException(404, "investigation not found")
        if inv.status in ("completed", "failed", "cancelled"):
            return {"id": rid, "status": inv.status}
        inv.status = "cancelled"
        inv.stage = "cancelled"
        try:
            evts = json.loads(inv.events or "[]")
        except Exception:
            evts = []
        evts.append({"ts": now_iso(), "stage": "cancelled", "message": "Cancelled by user.", "kind": "warn"})
        inv.events = json.dumps(evts)
        db.commit()
        return {"id": rid, "status": "cancelled", "job_stopped": stopped}
    finally:
        db.close()


@router.post("/research/{rid}/retry")
def retry_research(rid: str):
    db = _db()
    try:
        inv = db.get(Investigation, rid)
        if not inv:
            raise HTTPException(404, "investigation not found")
        if inv.status not in ("failed", "cancelled"):
            raise HTTPException(409, f"only failed/cancelled investigations can be retried (status={inv.status})")
        inv.status = "queued"
        inv.stage = "queued"
        inv.error = ""
        inv.retriable = 0
        db.commit()
    finally:
        db.close()
    jobs.submit(rid, lambda: run_pipeline(rid))
    return {"id": rid, "status": "queued"}


def _disc_dict(d: Discovery) -> dict:
    return {"id": d.id, "investigation_id": d.investigation_id, "headline": d.headline, "finding": d.finding,
            "significance": json.loads(d.significance_json or "[]"),
            "key_numbers": json.loads(d.key_numbers_json or "[]"),
            "timeline": json.loads(d.timeline_json or "[]"),
            "counterargument": json.loads(d.counterargument_json or "{}"),
            "falsification": json.loads(d.falsification_json or "{}"),
            "strength": d.strength, "strength_rationale": d.strength_rationale,
            "limitations": json.loads(d.limitations_json or "[]"),
            "coverage": json.loads(d.coverage_json or "{}"), "created_at": d.created_at}


@router.get("/discoveries/{did}")
def get_discovery(did: str):
    db = _db()
    try:
        d = db.get(Discovery, did)
        if not d:
            raise HTTPException(404, "discovery not found")
        inv = db.get(Investigation, d.investigation_id)
        out = _disc_dict(d)
        out["company"] = {"name": inv.company_name, "ticker": inv.ticker, "exchange": inv.exchange,
                          "track": inv.track, "period": inv.period} if inv else {}
        return out
    finally:
        db.close()


@router.get("/discoveries/{did}/evidence")
def get_evidence(did: str):
    db = _db()
    try:
        d = db.get(Discovery, did)
        if not d:
            raise HTTPException(404, "discovery not found")
        iid = d.investigation_id
        sources = db.query(Source).filter_by(investigation_id=iid).all()
        evs = db.query(Evidence).filter_by(investigation_id=iid).all()
        mets = db.query(Metric).filter_by(investigation_id=iid).all()
        hyps = db.query(Hypothesis).filter_by(investigation_id=iid).all()
        ev_by_src: dict[str, list] = {}
        for e in evs:
            ev_by_src.setdefault(e.source_id, []).append(
                {"id": e.id, "claim": e.claim, "passage": e.passage, "page_section": e.page_section,
                 "line_item": e.line_item, "reporting_period": e.reporting_period, "units": e.units,
                 "confidence": e.confidence, "kind": e.kind, "validation": e.validation})
        return {
            "sources": [{"id": s.id, "url": s.url, "title": s.title, "publisher": s.publisher,
                         "pub_date": s.pub_date, "retrieved_at": s.retrieved_at, "doc_type": s.doc_type,
                         "reporting_period": s.reporting_period, "extraction_status": s.extraction_status,
                         "role": s.role, "evidence": ev_by_src.get(s.id, [])} for s in sources],
            "metrics": [{"id": m.id, "name": m.name, "formula": m.formula_id, "inputs": json.loads(m.inputs_json or "{}"),
                         "evidence_ids": json.loads(m.evidence_ids_json or "[]"), "value": m.value, "units": m.units,
                         "period": m.period, "code_version": m.code_version} for m in mets],
            "hypotheses": [{"id": h.id, "text": h.text, "mechanism": h.mechanism,
                            "supporting": json.loads(h.supporting_json or "[]"),
                            "contradicting": json.loads(h.contradicting_json or "[]"),
                            "alternatives": json.loads(h.alternatives_json or "[]"),
                            "status": h.status, "rationale": h.rationale} for h in hyps],
        }
    finally:
        db.close()


@router.get("/discoveries/{did}/export", response_class=HTMLResponse)
def export_discovery(did: str):
    db = _db()
    try:
        d = db.get(Discovery, did)
        if not d:
            raise HTTPException(404, "discovery not found")
        inv = db.get(Investigation, d.investigation_id)
        sources = db.query(Source).filter_by(investigation_id=d.investigation_id).all()
        mets = db.query(Metric).filter_by(investigation_id=d.investigation_id).all()
        return render_html(_disc_dict(d),
                           {"company_name": inv.company_name, "ticker": inv.ticker, "track": inv.track,
                            "period": inv.period, "id": inv.id} if inv else {},
                           [{"url": s.url, "title": s.title, "publisher": s.publisher, "doc_type": s.doc_type,
                             "retrieved_at": s.retrieved_at} for s in sources],
                           [{"name": m.name, "value": m.value} for m in mets])
    finally:
        db.close()


@router.get("/history")
def history(search: str = "", track: str = "", status: str = "",
            limit: int = Query(default=50, le=200), offset: int = 0):
    db = _db()
    try:
        q = db.query(Investigation).order_by(Investigation.created_at.desc())
        if search:
            like = f"%{search}%"
            q = q.filter((Investigation.company_name.like(like)) | (Investigation.ticker.like(like)))
        if track:
            q = q.filter_by(track=track)
        if status:
            q = q.filter_by(status=status)
        total = q.count()
        invs = q.offset(offset).limit(limit).all()
        items = []
        for inv in invs:
            d = _inv_dict(inv)
            d.pop("error", None)
            if inv.discovery_id:
                disc = db.get(Discovery, inv.discovery_id)
                if disc:
                    d["headline"] = disc.headline
                    d["strength"] = disc.strength
            try:
                srcs = db.query(Source).filter_by(investigation_id=inv.id).all()
                d["source_coverage"] = {"n_sources": len(srcs),
                                        "n_publishers": len({s.publisher for s in srcs if s.publisher})}
            except Exception:
                d["source_coverage"] = {}
            items.append(d)
        return {"total": total, "items": items}
    finally:
        db.close()
