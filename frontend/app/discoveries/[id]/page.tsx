"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";
import { MetricChart } from "@/components/charts";
import { api, strengthColor } from "@/lib/api";
import { ExternalLink, Printer, ChevronDown, FlaskConical, AlertCircle, RotateCcw } from "lucide-react";

function Section({ id, n, title, children }: { id: string; n: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="card p-6 md:p-7 scroll-mt-24">
      <div className="flex items-baseline gap-3 mb-4">
        <span className="text-accent font-semibold text-sm num">{n}</span>
        <h2 className="text-[19px] font-semibold tracking-tight">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function DiscoveryPage() {
  const { id } = useParams<{ id: string }>();
  const [d, setD] = useState<any>(null);
  const [ev, setEv] = useState<any>(null);
  const [err, setErr] = useState("");
  const [openSrc, setOpenSrc] = useState<string | null>(null);

  function load() {
    setErr("");
    api.discovery(id).then(setD).catch((e) => setErr(e.message || "Failed to load discovery details."));
    api.evidence(id).then(setEv).catch(() => {});
  }

  useEffect(() => {
    load();
  }, [id]);

  const charts = useMemo(() => {
    if (!d?.key_numbers?.length) return [];
    const groups: Record<string, { period: string; value: number }[]> = {};
    for (const k of d.key_numbers) {
      const m = String(k.metric).split(" (")[0];
      const v = typeof k.value === "number" ? k.value : parseFloat(k.value);
      if (!isFinite(v)) continue;
      (groups[m] ||= []).push({ period: String(k.periods || k.metric), value: v });
    }
    return Object.entries(groups).map(([m, data]) => ({ metric: m, data }));
  }, [d]);

  if (err) return (
    <div>
      <Nav />
      <main className="max-w-[1240px] mx-auto px-6 py-16">
        <div className="card p-6 border-neg/40 bg-neg/10 max-w-xl mx-auto text-center space-y-4">
          <AlertCircle size={32} className="text-neg mx-auto" />
          <div>
            <h2 className="text-lg font-semibold text-neg">Unable to load report</h2>
            <p className="text-sm text-sec mt-1">{err}</p>
          </div>
          <button onClick={load} className="border border-neg/40 hover:bg-neg/20 px-4 py-2 rounded-md text-sm font-medium inline-flex items-center gap-2 text-neg">
            <RotateCcw size={15} /> Try again
          </button>
        </div>
      </main>
    </div>
  );

  if (!d) return <div><Nav /><main className="max-w-[1240px] mx-auto px-6 py-12 space-y-3">{[1,2,3,4].map((i)=><div key={i} className="skel h-40"/>)}</main></div>;

  const srcById: Record<string, any> = Object.fromEntries((ev?.sources ?? []).map((s: any) => [s.id, s]));
  const toc = [["overview","A · Overview"],["why","B · Why it matters"],["numbers","C · Key numbers"],["charts","D · Charts"],["timeline","E · Timeline"],["evidence","F · Evidence trail"],["counter","G · Counterargument"],["falsify","H · Falsification"],["strength","I · Evidence strength"],["sources","J · Sources & methodology"]];

  return (
    <div>
      <Nav />
      <main className="max-w-[1240px] mx-auto px-6 py-10 grid lg:grid-cols-[200px_1fr] gap-8">
        <aside className="hidden lg:block">
          <nav className="sticky top-24 space-y-1 text-[13px]">
            {toc.map(([a, t]) => <a key={a} href={`#${a}`} className="block px-3 py-1.5 rounded text-sec hover:text-pri hover:bg-surf2">{t}</a>)}
            <a href={api.exportUrl(id)} target="_blank" className="flex items-center gap-2 px-3 py-2 mt-3 border border-line rounded text-pri hover:bg-surf2"><Printer size={13} /> Print / PDF</a>
          </nav>
        </aside>

        <div className="space-y-6 min-w-0">
          <Section id="overview" n="A" title="Discovery overview">
            <h1 className="text-[30px] md:text-[36px] leading-[1.15] font-semibold tracking-[-0.02em]">{d.headline}</h1>
            <p className="text-sec text-[15px] leading-[1.55] mt-3 max-w-3xl">{d.finding}</p>
            <div className="flex flex-wrap gap-2 mt-4 text-[12px]">
              <span className={`px-2.5 py-1 rounded border font-medium ${strengthColor(d.strength)}`}>{d.strength} evidence</span>
              <span className="px-2.5 py-1 rounded border border-line text-sec">{d.company?.name} ({d.company?.ticker}) · Track {d.company?.track}</span>
              <span className="px-2.5 py-1 rounded border border-line text-sec num">{d.company?.period} · {String(d.created_at).slice(0, 16).replace("T", " ")}</span>
              <span className="px-2.5 py-1 rounded border border-line text-sec num">{d.coverage?.n_sources ?? 0} sources · {d.coverage?.n_metrics ?? 0} metrics</span>
            </div>
          </Section>

          <Section id="why" n="B" title="Why it matters">
            <ul className="list-disc pl-5 space-y-2 text-[14px] text-pri/90">
              {(d.significance ?? []).map((s: string, i: number) => <li key={i}>{s}</li>)}
            </ul>
          </Section>

          <Section id="numbers" n="C" title="Key numbers — every figure traceable">
            <div className="overflow-x-auto">
              <table className="fin">
                <thead><tr><th>Metric</th><th className="n">Value</th><th>Units</th><th>Periods</th><th>Formula</th><th>Sources</th></tr></thead>
                <tbody>
                  {(d.key_numbers ?? []).map((k: any, i: number) => (
                    <tr key={i}>
                      <td className="font-medium">{k.metric}</td>
                      <td className="n text-accent font-semibold">{typeof k.value === "number" ? k.value.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : k.value}</td>
                      <td className="text-sec">{k.units}</td>
                      <td className="text-sec num">{k.periods}</td>
                      <td className="text-ter text-[12px]">{k.formula}</td>
                      <td>{(k.source_ids ?? []).map((sid: string) => srcById[sid] ? (
                        <a key={sid} href={srcById[sid].url} target="_blank" rel="noreferrer" className="text-accent text-[12px] mr-2 inline-flex items-center gap-0.5">↗ {srcById[sid].publisher || "source"}</a>
                      ) : null)}</td>
                    </tr>
                  ))}
                  {!(d.key_numbers ?? []).length && <tr><td colSpan={6} className="text-ter text-sm">No validated numbers — see limitations.</td></tr>}
                </tbody>
              </table>
            </div>
          </Section>

          {!!charts.length && (
            <div id="charts" className="scroll-mt-24">
              <div className="flex items-baseline gap-3 mb-4 px-1"><span className="text-accent font-semibold text-sm num">D</span>
                <h2 className="text-[19px] font-semibold tracking-tight">Financial charts</h2></div>
              <div className="grid md:grid-cols-2 gap-4">
                {charts.map((c) => <MetricChart key={c.metric} title={c.metric} data={c.data} source={(ev?.sources ?? []).find((s: any) => (s.url || "").includes("screener"))?.publisher || "audited filings via Screener.in"} />)}
              </div>
            </div>
          )}

          <Section id="timeline" n="E" title="Timeline">
            <ol className="relative border-l border-line ml-2 space-y-4">
              {(d.timeline ?? []).map((t: any, i: number) => (
                <li key={i} className="ml-4">
                  <span className="absolute -left-[5px] mt-1.5 w-2.5 h-2.5 rounded-full bg-accent/70" />
                  <div className="text-[12px] text-ter num">{t.date} · {t.kind}</div>
                  <div className="text-sm mt-0.5">{t.label}</div>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="evidence" n="F" title="Evidence trail — click any claim">
            {!ev ? <div className="skel h-24" /> : (ev.sources ?? []).map((s: any) => (
              <div key={s.id} className="border border-line/70 rounded-md mb-2.5 overflow-hidden">
                <button onClick={() => setOpenSrc(openSrc === s.id ? null : s.id)} className="w-full text-left px-4 py-3 flex items-center gap-2 hover:bg-surf2">
                  <ChevronDown size={14} className={`text-ter transition-transform ${openSrc === s.id ? "rotate-180" : ""}`} />
                  <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${s.role === "contradictory" ? "text-warn border-warn/40" : "text-sec border-line"}`}>{s.doc_type} · {s.role}</span>
                  <span className="text-sm font-medium truncate">{s.title || s.url}</span>
                  <a href={s.url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="ml-auto text-accent shrink-0"><ExternalLink size={13} /></a>
                </button>
                {openSrc === s.id && (
                  <div className="px-4 pb-4 pt-1 space-y-2.5 border-t border-line/60">
                    <div className="text-[11px] text-ter">{s.publisher} · retrieved {String(s.retrieved_at).slice(0, 16).replace("T", " ")} · {s.extraction_status}</div>
                    {(s.evidence ?? []).map((e: any) => (
                      <figure key={e.id} className="bg-surf2 border border-line rounded p-3">
                        <blockquote className="text-[13px] leading-relaxed">“{e.passage}”</blockquote>
                        <figcaption className="text-[11px] text-ter mt-1.5">{e.line_item} · {e.page_section} · confidence {Math.round((e.confidence ?? 0) * 100)}% · {e.kind}/{e.validation}</figcaption>
                      </figure>
                    ))}
                    {!(s.evidence ?? []).length && <p className="text-[12px] text-ter">No passages extracted from this document.</p>}
                  </div>
                )}
              </div>
            ))}
            <div className="mt-4">
              <div className="label mb-2">Competing hypotheses</div>
              {(ev?.hypotheses ?? []).map((h: any) => (
                <div key={h.id} className="text-[13px] border border-line/70 rounded-md p-3 mb-2">
                  <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border mr-2 ${h.status === "validated" ? "text-pos border-pos/40" : h.status === "ruled_out" ? "text-neg border-neg/40" : "text-warn border-warn/40"}`}>{h.status}</span>
                  {h.text}
                  <div className="text-[11px] text-ter mt-1">{h.mechanism}</div>
                </div>
              ))}
            </div>
          </Section>

          <Section id="counter" n="G" title="Counterargument">
            <p className="text-sm"><b>{d.counterargument?.strongest_alternative}</b></p>
            <p className="text-sm text-sec mt-2">{d.counterargument?.why_plausible}</p>
            <p className="text-[13px] mt-2">Verdict: <span className="font-medium text-warn">{d.counterargument?.verdict}</span></p>
            {!!(d.counterargument?.all_alternatives ?? []).length && (
              <ul className="list-disc pl-5 mt-2 text-[13px] text-sec">{d.counterargument.all_alternatives.map((a: string, i: number) => <li key={i}>{a}</li>)}</ul>
            )}
          </Section>

          <Section id="falsify" n="H" title="Falsification condition">
            <div className="flex gap-3 items-start">
              <FlaskConical size={16} className="text-accent mt-0.5 shrink-0" />
              <div className="text-sm">
                <p>{d.falsification?.condition}</p>
                <p className="text-[12px] text-ter mt-2 num">metric: {d.falsification?.metric} · baseline: {d.falsification?.baseline} · threshold: {d.falsification?.threshold} · {d.falsification?.period}</p>
              </div>
            </div>
          </Section>

          <Section id="strength" n="I" title="Evidence strength">
            <p className="text-sm"><span className={`px-2 py-0.5 rounded border font-medium ${strengthColor(d.strength)}`}>{d.strength}</span></p>
            <p className="text-sm text-sec mt-2">{d.strength_rationale}</p>
            {!!(d.limitations ?? []).length && (
              <><div className="label mt-4 mb-2">Limitations</div>
                <ul className="list-disc pl-5 text-[13px] text-sec space-y-1">{d.limitations.map((l: string, i: number) => <li key={i}>{l}</li>)}</ul></>
            )}
          </Section>

          <Section id="sources" n="J" title="Sources & methodology">
            <div className="label mb-2">Calculation provenance (finlib-v1)</div>
            <div className="overflow-x-auto mb-4">
              <table className="fin">
                <thead><tr><th>Metric</th><th className="n">Value</th><th>Period</th><th>Formula</th><th>Inputs</th></tr></thead>
                <tbody>
                  {(ev?.metrics ?? []).map((m: any) => (
                    <tr key={m.id}><td className="font-medium">{m.name}</td>
                      <td className="n num">{typeof m.value === "number" ? m.value.toLocaleString("en-IN", { maximumFractionDigits: 4 }) : m.value}</td>
                      <td className="text-sec num">{m.period}</td><td className="text-ter text-[12px]">{m.formula}</td>
                      <td className="text-ter text-[12px] num">{JSON.stringify(m.inputs)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ol className="list-decimal pl-5 space-y-1.5 text-[13px]">
              {(ev?.sources ?? []).map((s: any) => (
                <li key={s.id}><a href={s.url} target="_blank" rel="noreferrer" className="text-accent hover:underline">{s.title || s.url}</a>
                  <span className="text-ter"> — {s.publisher} · {s.doc_type} · retrieved {String(s.retrieved_at).slice(0, 10)}</span></li>
              ))}
            </ol>
            <p className="text-[12px] text-ter mt-4">Research tool — not investment advice. Verify every figure against the linked primary sources before acting. <a className="text-accent" href="/methodology">Methodology →</a></p>
          </Section>
        </div>
      </main>
    </div>
  );
}
