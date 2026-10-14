"use client";
import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { StageBar } from "@/components/charts";
import { api } from "@/lib/api";
import { ExternalLink, Ban, RotateCcw, AlertCircle } from "lucide-react";

type Evt = { ts: string; stage: string; message: string; kind: string };

export default function ResearchWorkspace() {
  const { id } = useParams<{ id: string }>();
  const r = useRouter();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const es = useRef<EventSource | null>(null);

  async function poll() {
    try {
      const d = await api.research(id);
      setData(d);
      setErr("");
      if (d.status === "completed" && d.discovery_id) {
        es.current?.close();
        r.replace(`/discoveries/${d.discovery_id}`);
      }
      return d.status;
    } catch (e: any) {
      setErr(e.message || "Failed to fetch investigation updates.");
      return "error";
    }
  }

  useEffect(() => {
    poll();
    const t = setInterval(async () => {
      const s = await poll();
      if (s === "completed" || s === "failed" || s === "cancelled") clearInterval(t);
    }, 2500);
    try {
      const src = new EventSource(api.eventsUrl(id));
      es.current = src;
      src.addEventListener("done", () => { poll(); src.close(); clearInterval(t); });
      src.onerror = () => {
        // EventSource reconnection error handling
      };
    } catch { /* polling fallback covers it */ }
    return () => { clearInterval(t); es.current?.close(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const events: Evt[] = data?.events ?? [];

  return (
    <div>
      <Nav active="/research/new" />
      <main className="max-w-[1240px] mx-auto px-6 py-10">
        {err && (
          <div className="mb-6 border border-neg/40 bg-neg/10 text-neg rounded-md p-4 flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0 text-neg" />
              <span>{err}</span>
            </div>
            <button onClick={() => poll()} className="border border-neg/40 hover:bg-neg/20 px-3 py-1 rounded text-xs font-medium shrink-0">
              Retry Connection
            </button>
          </div>
        )}

        {!data ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="skel h-16" />)}</div>
        ) : (
          <>
            <div className="flex flex-wrap items-start gap-4">
              <div>
                <h1 className="text-[28px] font-semibold tracking-tight">{data.company_name} <span className="text-sec num text-lg">({data.ticker})</span></h1>
                <p className="text-sec text-sm mt-1">Track {data.track} · {data.period} · {data.depth} · {data.exchange} · started {String(data.created_at).slice(0, 16).replace("T", " ")}</p>
              </div>
              <div className="ml-auto flex gap-2">
                {(data.status === "running" || data.status === "queued") && (
                  <button onClick={() => api.cancel(id).then(poll)} className="border border-line text-sm px-4 py-2 rounded-md hover:bg-surf2 inline-flex items-center gap-2"><Ban size={14} /> Cancel</button>
                )}
                {(data.status === "failed" || data.status === "cancelled") && (
                  <button onClick={() => api.retry(id).then(poll)} className="border border-accent/50 text-accent text-sm px-4 py-2 rounded-md inline-flex items-center gap-2"><RotateCcw size={14} /> Retry</button>
                )}
              </div>
            </div>

            <div className="card p-5 mt-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="label">Stage</span>
                <span className={`text-[11px] px-2 py-0.5 rounded border uppercase tracking-wide ${data.status === "completed" ? "text-pos border-pos/40" : data.status === "failed" ? "text-neg border-neg/40" : "text-accent border-accent/40"}`}>{data.status}</span>
                {data.status === "running" && <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />}
              </div>
              <StageBar stages={data.stages} index={data.stage_index} status={data.status} />
              {data.error && (
                <div className="text-sm border border-neg/40 bg-neg/10 text-neg rounded-md p-3.5 mt-4 flex items-start gap-2.5">
                  <AlertCircle size={16} className="shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold mb-0.5">Pipeline execution failed</div>
                    <div>{data.error}</div>
                  </div>
                </div>
              )}
            </div>

            <div className="grid lg:grid-cols-2 gap-6 mt-6">
              <div className="card p-5">
                <div className="label mb-3">Research plan</div>
                {!data.plan?.length ? <div className="skel h-10" /> :
                  <ul className="space-y-3">
                    {data.plan.map((p: any) => (
                      <li key={p.id} className="border border-line/70 rounded-md p-3">
                        <div className="text-sm font-medium">{p.id} · {p.question}</div>
                        <div className="text-[12px] text-sec mt-1">{p.why}</div>
                        <div className="text-[11px] text-ter mt-1 num">priority {p.priority}/10 · disprove: {p.disprove_test}</div>
                      </li>
                    ))}
                  </ul>}
                {!!data.patterns?.length && (
                  <div><div className="label mt-5 mb-3">Validated patterns (deterministic)</div>
                    <ul className="space-y-2">
                      {data.patterns.map((p: any, i: number) => (
                        <li key={i} className="text-[13px] border border-pos/30 bg-pos/5 rounded-md p-3">
                          <span className="text-pos font-medium num">{p.id}</span> · {p.reason}
                          <div className="text-[11px] text-ter mt-1">calc: {p.calc}</div>
                        </li>
                      ))}
                    </ul></div>)}
              </div>
              <div className="card p-5">
                <div className="label mb-3">Live evidence stream</div>
                <ul className="space-y-2 max-h-[560px] overflow-auto pr-1">
                  {[...events].reverse().map((e, i) => (
                    <li key={i} className={`text-[13px] border rounded-md px-3 py-2 ${e.kind === "error" ? "border-neg/40 text-neg" : e.kind === "warn" ? "border-warn/30 text-warn" : "border-line/70 text-sec"}`}>
                      <span className="text-[10px] uppercase tracking-wider text-ter mr-2">{e.stage}</span>{e.message}
                    </li>
                  ))}
                  {!events.length && <div className="skel h-10" />}
                </ul>
                <p className="text-[11px] text-ter mt-3">Only backend-reported states are shown — no simulated progress. Full source inspection opens with the report.</p>
                {data.discovery_id && <a href={`/discoveries/${data.discovery_id}`} className="text-accent text-sm mt-2 inline-flex items-center gap-1">Open discovery <ExternalLink size={13} /></a>}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
