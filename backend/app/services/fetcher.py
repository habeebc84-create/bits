"""URL fetching + text extraction + source dedup/normalization.

- SSRF guard on every URL, timeouts, byte cap, retries, rate limit-friendly.
- HTML via trafilatura (fallback BeautifulSoup); PDF via PyMuPDF.
- Treats all retrieved content as untrusted data (no prompt injection into reasoning).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
import re
import time
import urllib.parse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .ssrf import is_safe_url

log = logging.getLogger("signalhunter.fetch")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SignalHunterX/1.0 (research-tool)"}
_last_hit = 0.0


def _polite():
    global _last_hit
    gap = time.time() - _last_hit
    if gap < 1.0:
        time.sleep(1.0 - gap)
    _last_hit = time.time()


def canonicalize(url: str) -> str:
    p = urllib.parse.urlparse(url.strip())
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=False)
    drop = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
    q = [(k, v) for k, v in q if k.lower() not in drop]
    return urllib.parse.urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", "", urllib.parse.urlencode(sorted(q)), ""))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:32]


def dedupe_sources(items: list[dict]) -> list[dict]:
    """Drop duplicate canonical URLs and near-duplicate content (same hash prefix)."""
    seen_url, seen_hash, out = set(), set(), []
    for it in items:
        cu = canonicalize(it.get("url", ""))
        if not cu or cu in seen_url:
            continue
        h = it.get("content_hash", "")
        if h and h in seen_hash:
            continue
        seen_url.add(cu)
        if h:
            seen_hash.add(h)
        it["canonical_url"] = cu
        out.append(it)
    return out


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=6))
def fetch_url(url: str) -> dict:
    s = get_settings()
    ok, reason = is_safe_url(url)
    if not ok:
        return {"ok": False, "error": f"blocked: {reason}", "url": url}
    _polite()
    try:
        with httpx.Client(timeout=s.FETCH_TIMEOUT_S, headers=UA, follow_redirects=True, max_redirects=5) as c:
            r = c.get(url)
            ctype = r.headers.get("content-type", "").lower()
            if len(r.content) > s.FETCH_MAX_BYTES:
                return {"ok": False, "error": "payload too large", "url": url}
            if r.status_code >= 400:
                return {"ok": False, "error": f"http {r.status_code}", "url": url}
            return {"ok": True, "url": str(r.url), "content_type": ctype, "content": r.content, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "url": url}


def extract_text(fetched: dict) -> dict:
    """Returns {text, kind} — kind in {html, pdf, other}. Never invents content."""
    if not fetched.get("ok"):
        return {"text": "", "kind": "other", "error": fetched.get("error", "fetch failed")}
    ctype: str = fetched.get("content_type", "")
    raw: bytes = fetched.get("content", b"")
    if "pdf" in ctype or fetched["url"].lower().endswith(".pdf"):
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=raw, filetype="pdf")
            pages = []
            for i, page in enumerate(doc):
                t = page.get_text("text") or ""
                if t.strip():
                    pages.append(f"[p.{i+1}] {t.strip()}")
                if sum(len(p) for p in pages) > 120_000:
                    break
            return {"text": "\n".join(pages)[:120_000], "kind": "pdf"}
        except Exception as e:
            return {"text": "", "kind": "pdf", "error": f"pdf extract failed: {e}"[:200]}
    # HTML
    html = raw.decode("utf-8", "ignore")
    text = ""
    try:
        from trafilatura import extract as trafi

        text = trafi(html, include_comments=False, include_tables=True) or ""
    except Exception:
        text = ""
    if len(text.strip()) < 200:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(" ", strip=True)
        except Exception:
            pass
    text = re.sub(r"\s+", " ", text).strip()[:60_000]
    return {"text": text, "kind": "html"}


_FIN_PATTERNS = [
    # (label regex, unit-normalized crore INR extraction handled in finance.py)
    r"(total income|total revenue|revenue from operations|net sales)",
    r"(net profit|profit after tax|pat\b)",
    r"(ebitda|operating profit|pbidtm?)",
    r"(net interest income|nii\b)",
    r"(gross npa|gnpa|net npa|nnpa|provision)",
    r"(ebitda margin|net profit margin|pat margin|nim\b)",
    r"(return on equity|roe\b|return on assets|roa\b)",
    r"(debt|borrowings|equity|net worth)",
    r"(eps|dividend|capex|order book|capacity|generation|plf|volume)",
]


def extract_passages(text: str, max_passages: int = 8) -> list[dict]:
    """Pull sentences containing financial line-item mentions + any explicit figures.

    Returns [{passage, line_item, figures}] with verbatim quotes only.
    """
    if not text:
        return []
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    scored = []
    fig_re = re.compile(r"(₹|Rs\.?|INR)?\s?[\d,]+(\.\d+)?\s?(crore|cr|lakh|million|billion|%)?", re.I)
    for s in sents:
        s2 = s.strip()
        if len(s2) < 40 or len(s2) > 600:
            continue
        hits = [p for p in _FIN_PATTERNS if re.search(p, s2, re.I)]
        figs = fig_re.findall(s2)
        has_fig = any(any(x) for x in figs)
        if hits and (has_fig or len(s2) < 300):
            scored.append({"passage": s2, "line_item": hits[0].strip("^$")[:80], "figures": has_fig, "score": len(hits) * 2 + (1 if has_fig else 0)})
    scored.sort(key=lambda d: -d["score"])
    return [{k: d[k] for k in ("passage", "line_item", "figures")} for d in scored[:max_passages]]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()
