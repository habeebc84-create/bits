"""Report export: professional print-ready HTML (print-to-PDF) with clickable links."""
from __future__ import annotations

import html
import json


def _e(s) -> str:
    return html.escape(str(s))


def render_html(discovery: dict, inv: dict, sources: list[dict], metrics: list[dict]) -> str:
    d = discovery
    kn = "\n".join(
        f"<tr><td>{_e(k.get('metric',''))}</td><td class=num>{_e(k.get('value',''))}</td>"
        f"<td>{_e(k.get('units',''))}</td><td>{_e(k.get('periods',''))}</td><td class=small>{_e(k.get('formula',''))}</td></tr>"
        for k in d.get("key_numbers", [])
    )
    src = "\n".join(
        f"<li><a href='{_e(s.get('url',''))}'>{_e(s.get('title','') or s.get('url',''))}</a> "
        f"<span class=small>— {_e(s.get('publisher',''))} · {_e(s.get('doc_type',''))} · retrieved {_e(s.get('retrieved_at',''))}</span></li>"
        for s in sources
    )
    tl = "\n".join(f"<li><b>{_e(t.get('date',''))}</b> — {_e(t.get('label',''))}</li>" for t in d.get("timeline", []))
    sig = "\n".join(f"<li>{_e(s)}</li>" for s in d.get("significance", []))
    lim = "\n".join(f"<li>{_e(s)}</li>" for s in d.get("limitations", []))
    ca = d.get("counterargument", {})
    fa = d.get("falsification", {})
    return f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>SIGNAL HUNTER X — {_e(d.get('headline',''))}</title>
<style>body{{font-family:Inter,Arial,sans-serif;max-width:860px;margin:40px auto;color:#111;line-height:1.6;padding:0 20px}}
.cover{{border-bottom:3px solid #0e7490;padding-bottom:16px;margin-bottom:24px}}.brand{{font-size:12px;letter-spacing:2px;color:#0e7490;font-weight:700}}
h1{{font-size:28px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:6px 8px;font-size:13px;text-align:left}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}.small{{font-size:12px;color:#444}}.badge{{display:inline-block;background:#0e7490;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px}}
@media print{{body{{margin:0}}}}a{{color:#0e7490}}</style></head><body>
<div class=cover><div class=brand>SIGNAL HUNTER X · AUTONOMOUS FINANCIAL INTELLIGENCE</div>
<h1>{_e(d.get('headline',''))}</h1>
<p><span class=badge>{_e(d.get('strength',''))}</span> &nbsp; {_e(inv.get('company_name',''))} ({_e(inv.get('ticker',''))}) · Track {_e(inv.get('track',''))} · {_e(inv.get('period',''))} · Investigation {_e(inv.get('id',''))} · {_e(d.get('created_at',''))}</p></div>
<h2>Discovery</h2><p>{_e(d.get('finding',''))}</p>
<h2>Why it matters</h2><ul>{sig}</ul>
<h2>Key numbers</h2><table><tr><th>Metric</th><th>Value</th><th>Units</th><th>Periods</th><th>Formula</th></tr>{kn}</table>
<h2>Timeline</h2><ul>{tl}</ul>
<h2>Counterargument</h2><p><b>{_e(ca.get('strongest_alternative',''))}</b> — {_e(ca.get('why_plausible',''))} Verdict: {_e(ca.get('verdict',''))}.</p>
<h2>Falsification condition</h2><p>{_e(fa.get('condition',''))} (metric: {_e(fa.get('metric',''))}; baseline: {_e(fa.get('baseline',''))}; threshold: {_e(fa.get('threshold',''))})</p>
<h2>Evidence strength</h2><p><b>{_e(d.get('strength',''))}</b> — {_e(d.get('strength_rationale',''))}</p>
<h2>Limitations</h2><ul>{lim}</ul>
<h2>Sources & methodology</h2><ol>{src}</ol>
<p class=small>Deterministic calculations: finlib-v1. Research tool — not investment advice. Verify every figure against linked primary sources before acting.</p>
</body></html>"""
