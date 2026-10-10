"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Nav from "@/components/Nav";
import { api, strengthColor } from "@/lib/api";
import { AlertCircle, RotateCcw } from "lucide-react";

export default function History() {
  const [q, setQ] = useState("");
  const [track, setTrack] = useState("");
  const [status, setStatus] = useState("");
  const [data, setData] = useState<{ total: number; items: any[] }>({ total: 0, items: [] });
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    try {
      setData(await api.history({ search: q, track, status }));
    } catch (e: any) {
      setErr(e.message || "Failed to load research history from server.");
    }
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  return (
    <div>
      <Nav active="/history" />
      <main className="max-w-[1240px] mx-auto px-6 py-12">
        <h1 className="text-[32px] font-semibold tracking-[-0.02em]">Research history</h1>
        <p className="text-sec text-sm mt-2">Saved investigations reopen without re-running. {data.total} total.</p>

        {err && (
          <div className="mt-6 border border-neg/40 bg-neg/10 text-neg rounded-md p-4 flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0 text-neg" />
              <span>{err}</span>
            </div>
            <button onClick={load} className="border border-neg/40 hover:bg-neg/20 px-3 py-1 rounded text-xs font-medium inline-flex items-center gap-1 shrink-0">
              <RotateCcw size={12} /> Retry
            </button>
          </div>
        )}

        <div className="flex flex-wrap gap-2 mt-6">
          <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="Search company or ticker…" className="bg-surf2 border border-line rounded-md px-3 py-2 text-sm w-64 placeholder:text-ter outline-none focus:border-accent" />
          <select value={track} onChange={(e) => setTrack(e.target.value)} className="bg-surf2 border border-line rounded-md px-3 py-2 text-sm">
            <option value="">All tracks</option>{["A","B","C","D"].map((t)=><option key={t} value={t}>Track {t}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="bg-surf2 border border-line rounded-md px-3 py-2 text-sm">
            <option value="">All statuses</option>{["queued","running","completed","failed","cancelled"].map((s)=><option key={s}>{s}</option>)}
          </select>
          <button onClick={load} className="border border-line text-sm px-4 py-2 rounded-md hover:bg-surf2">Filter</button>
        </div>
        <div className="card mt-6 overflow-x-auto">
          <table className="fin min-w-[860px]">
            <thead><tr><th>Company</th><th>Track</th><th>Date</th><th>Status</th><th>Discovery</th><th>Strength</th><th className="n">Sources</th><th></th></tr></thead>
            <tbody>
              {data.items.map((it) => (
                <tr key={it.id}>
                  <td className="font-medium">{it.company_name} <span className="text-ter num">{it.ticker}</span></td>
                  <td className="text-sec">{it.track}</td>
                  <td className="text-sec num text-[12px]">{String(it.created_at).slice(0, 10)}</td>
                  <td><span className={`text-[11px] px-2 py-0.5 rounded border uppercase ${it.status === "completed" ? "text-pos border-pos/40" : it.status === "failed" ? "text-neg border-neg/40" : "text-sec border-line"}`}>{it.status}</span></td>
                  <td className="text-sec text-[13px] max-w-[280px] truncate">{it.headline ?? "—"}</td>
                  <td>{it.strength && <span className={`text-[11px] px-2 py-0.5 rounded border ${strengthColor(it.strength)}`}>{it.strength}</span>}</td>
                  <td className="n num text-sec">{it.source_coverage?.n_sources ?? "—"}</td>
                  <td className="text-right whitespace-nowrap">
                    {it.discovery_id ? <Link href={`/discoveries/${it.discovery_id}`} className="text-accent text-[13px]">Report →</Link>
                      : <Link href={`/research/${it.id}`} className="text-accent text-[13px]">Workspace →</Link>}
                  </td>
                </tr>
              ))}
              {!data.items.length && !err && <tr><td colSpan={8} className="text-ter text-sm px-3 py-6">No investigations yet. <Link href="/research/new" className="text-accent">Launch one →</Link></td></tr>}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
