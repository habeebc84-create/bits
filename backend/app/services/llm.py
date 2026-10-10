"""LLM provider adapter. Interface is provider-agnostic; deterministic engine is the
default so the system works with zero keys. LLM (when configured) only *explains* —
finlib remains the calculator of record and every number is re-validated."""
from __future__ import annotations

import json
import logging

import httpx

from ..config import get_settings

log = logging.getLogger("signalhunter.llm")


def status() -> dict:
    s = get_settings()
    if s.LLM_PROVIDER == "openai_compatible" and s.LLM_API_KEY and s.LLM_BASE_URL and s.LLM_MODEL:
        return {"provider": "openai_compatible", "model": s.LLM_MODEL, "configured": True, "role": "explanation only; calculations stay deterministic"}
    return {"provider": "none", "model": "deterministic-engine", "configured": False, "role": "rule-based reasoning over verified calculations"}


def complete_json(system: str, user: str, max_tokens: int = 1500) -> dict | None:
    """Returns parsed JSON or None (caller must fall back). Never raises."""
    s = get_settings()
    if not (s.LLM_PROVIDER == "openai_compatible" and s.LLM_API_KEY and s.LLM_BASE_URL):
        return None
    try:
        with httpx.Client(timeout=60) as c:
            r = c.post(
                s.LLM_BASE_URL.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {s.LLM_API_KEY}", "Content-Type": "application/json"},
                json={"model": s.LLM_MODEL,
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                      "temperature": 0.2, "max_tokens": max_tokens,
                      "response_format": {"type": "json_object"}},
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        log.warning("llm call failed: %s", e)
        return None
