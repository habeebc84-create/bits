"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api, TRACKS, type CompanyHit } from "@/lib/api";
import { Search, Building2 } from "lucide-react";

export default function NewInvestigation() {
  const r = useRouter();
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<CompanyHit[]>([]);
  const [sel, setSel] = useState<CompanyHit | null>(null);
  const [exchange, setExchange] = useState("NSE");
  const [track, setTrack] = useState("C");
  const [period, setPeriod] = useState("FY2022-FY2025");
  const [depth, setDepth] = useState("standard");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const t = useRef<any>(null);

  useEffect(() => {
    clearTimeout(t.current);
    if (q.trim().length < 2) { setHits([]); return; }
    t.current = setTimeout(async () => {
      try { setHits((await api.searchCompanies(q)).results); } catch { /* offline */ }
    }, 250);
    return () => clearTimeout(t.current);
  }, [q]);

  async function start() {
    if (!sel) { setErr("Select a company from the suggestions."); return; }
    setBusy(true); setErr("");
    try {
      const { id } = await api.createResearch({ company: sel.ticker, exchange, track, period, depth });
      r.push(`/research/${id}`);
    } catch (e: any) { setErr(e.message); setBusy(false); }
  }

  return (
    <div>
      <Nav active="/research/new" />
      <main className="max-w-[1240px] mx-auto px-6 py-12 grid lg:grid-cols-[1fr_340px] gap-8">
        <div>
          <h1 className="text-[32px] font-semibold tracking-[-0.02em]">New investigation</h1>
          <p className="text-sec text-[15px] mt-2">The agent resolves the company, plans questions, retrieves public sources, calculates, and argues against itself.</p>

          <div className="card p-6 mt-8 space-y-5">
            <div>
              <div className="label mb-2">Company name or ticker</div>
              <div className="relative">
                <Search size={15} className="absolute left-3 top-3 text-ter" />
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. ITC, HDFCBANK, Sun Pharma…"
                  className="w-full bg-surf2 border border-line rounded-md pl-9 pr-3 py-2.5 text-sm placeholder:text-ter focus:border-accent outline-none" />
              </div>
              {!!hits.length && (
                <ul className="mt-2 border border-line rounded-md divide-y divide-line/60 bg-surf2 max-h-64 overflow-auto">
                  {hits.map((h) => (
                    <li key={h.ticker}>
                      <button onClick={() => { setSel(h); setTrack(h.track); setQ(`${h.canonical_name} (${h.ticker})`); setHits([]); }}
                        className="w-full text-left px-4 py-2.5 hover:bg-accent/5 flex items-center gap-3">
                        <Building2 size={15} className="text-ter shrink-0" />
                        <span><span className="text-sm font-medium">{h.canonical_name}</span>
                          <span className="text-[12px] text-ter ml-2 num">{h.ticker} · {h.sector} · Track {h.track}</span></span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <div className="label mb-2">Exchange</div>
                <div className="flex gap-2">
                  {["NSE", "BSE"].map((e) => (
                    <button key={e} onClick={() => setExchange(e)} className={`px-4 py-2 text-sm rounded-md border ${exchange === e ? "border-accent text-accent bg-accent/10" : "border-line text-sec"}`}>{e}</button>
                  ))}
                </div>
              </div>
              <div>
                <div className="label mb-2">Research period</div>
                <select value={period} onChange={(e) => setPeriod(e.target.value)} className="w-full bg-surf2 border border-line rounded-md px-3 py-2.5 text-sm">
                  {["FY2021-FY2024", "FY2022-FY2025", "FY2020-FY2025"].map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <div className="label mb-2">Sector track</div>
                <select value={track} onChange={(e) => setTrack(e)} className="w-full bg-surf2 border border-line rounded-md px-3 py-2.5 text-sm">
                  {Object.entries(TRACKS).map(([k, v]) => <option key={k} value={k}>Track {k} — {v}</option>)}
                </select>
              </div>
              <div>
                <div className="label mb-2">Investigation depth</div>
                <div className="flex gap-2">
                  {["quick", "standard", "deep"].map((d) => (
                    <button key={d} onClick={() => setDepth(d)} className={`px-4 py-2 text-sm rounded-md border capitalize ${depth === d ? "border-accent text-accent bg-accent/10" : "border-line text-sec"}`}>{d}</button>
                  ))}
                </div>
              </div>
            </div>
            {err && <div className="text-sm text-neg border border-neg/40 bg-neg/10 rounded-md px-4 py-2.5">{err}</div>}
            <button onClick={start} disabled={busy || !sel} className="bg-accent text-ink font-semibold text-sm px-6 py-2.5 rounded-md hover:brightness-110 disabled:opacity-40">
              {busy ? "Launching…" : "Start research"}
            </button>
          </div>
        </div>
        <aside className="card p-6 h-fit lg:sticky lg:top-24">
          <div className="label mb-3">Scope summary</div>
          {sel ? (
            <div className="space-y-2 text-sm">
              <div className="font-semibold">{sel.canonical_name}</div>
              <div className="text-sec num">{sel.ticker} · {exchange}</div>
              <div className="text-sec">{sel.sector} — {sel.industry}</div>
              <div className="text-sec">Track {track} · {TRACKS[track]}</div>
              <div className="text-sec num">{period} · {depth}</div>
            </div>
          ) : <p className="text-sm text-ter">Select a company to preview the research scope.</p>}
          <p className="text-[12px] text-ter mt-4 leading-relaxed">No buy/sell recommendations. Every claim cites a public source; insufficient evidence returns an honest inconclusive result.</p>
        </aside>
      </main>
    </div>
  );
}
