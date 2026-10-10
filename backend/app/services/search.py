"""Public web-search adapter: keyless built-in (DuckDuckGo) + optional Serper/Tavily.

Never fabricates results: on total failure returns [] and the pipeline records
a source-coverage limitation instead of inventing links.
"""
from __future__ import annotations

import logging
import re
import urllib.parse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

log = logging.getLogger("signalhunter.search")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SignalHunterX/1.0 (research-tool)"}


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _ddg_search(query: str, n: int = 10) -> list[dict]:
    """DuckDuckGo HTML endpoint (no key). Parses redirect links to real targets."""
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    with httpx.Client(timeout=20, headers=UA, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        html = r.text
    out: list[dict] = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, title_html = m.group(1), m.group(2)
        title = _clean(re.sub(r"<[^>]+>", "", title_html))
        # unwrap //duckduckgo.com/l/?uddg=<target>
        target = href
        mm = re.search(r"uddg=([^&]+)", href)
        if mm:
            target = urllib.parse.unquote(mm.group(1))
        if target.startswith("//"):
            target = "https:" + target
        if not target.startswith("http"):
            continue
        out.append({"title": title or target, "url": target, "publisher": urllib.parse.urlparse(target).netloc})
        if len(out) >= n:
            break
    return out


def _serper(query: str, n: int, key: str) -> list[dict]:
    with httpx.Client(timeout=20) as c:
        r = c.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": n},
        )
        r.raise_for_status()
        data = r.json()
    out = []
    for it in (data.get("organic") or [])[:n]:
        out.append({"title": it.get("title", ""), "url": it.get("link", ""), "publisher": urllib.parse.urlparse(it.get("link", "")).netloc})
    return [o for o in out if o["url"].startswith("http")]


def _tavily(query: str, n: int, key: str) -> list[dict]:
    with httpx.Client(timeout=25) as c:
        r = c.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": key, "query": query, "max_results": n, "search_depth": "advanced"},
        )
        r.raise_for_status()
        data = r.json()
    out = []
    for it in (data.get("results") or [])[:n]:
        out.append({"title": it.get("title", ""), "url": it.get("url", ""), "publisher": urllib.parse.urlparse(it.get("url", "")).netloc})
    return [o for o in out if o["url"].startswith("http")]


def web_search(query: str, n: int = 10) -> list[dict]:
    s = get_settings()
    try:
        if s.SEARCH_PROVIDER == "serper" and s.SERPER_API_KEY:
            return _serper(query, n, s.SERPER_API_KEY)
        if s.SEARCH_PROVIDER == "tavily" and s.TAVILY_API_KEY:
            return _tavily(query, n, s.TAVILY_API_KEY)
        return _ddg_search(query, n)
    except Exception as e:  # never crash pipeline on search failure
        log.warning("search failed q=%r err=%s", query[:80], e)
        return []


def discovery_queries(company_name: str, ticker: str, track: str) -> list[tuple[str, str]]:
    """(query, doc_type_hint) pairs. Generic across companies."""
    c = f"{company_name} {ticker}"
    base = [
        (f"{c} annual report investor relations", "annual_report"),
        (f"{c} quarterly results profit revenue", "results"),
        (f"{c} investor presentation", "presentation"),
        (f"{c} earnings call transcript", "transcript"),
        (f"{c} NSE filing announcement", "filing"),
    ]
    track_q = {
        "A": [(f"{c} NIM GNPA credit cost CASA", "results"), (f"{c} provisioning slippages", "filing")],
        "B": [(f"{c} capacity addition generation PLF", "results"), (f"{c} tariff PPA renewable", "industry")],
        "C": [(f"{c} volume growth margin gross margin", "results"), (f"{c} same store sales rural demand", "news")],
        "D": [(f"{c} US generics ANDA pipeline", "results"), (f"{c} USFDA inspection warning letter", "news")],
    }
    return base + track_q.get(track, [])
