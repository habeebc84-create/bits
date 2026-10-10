"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function Settings() {
  const [cfg, setCfg] = useState<any>(null);
  useEffect(() => { api.config().then(setCfg).catch(() => setCfg({ offline: true })); }, []);

  return (
    <div>
      <Nav active="/settings" />
      <main className="max-w-[1240px] mx-auto px-6 py-12 max-w-3xl">
        <h1 className="text-[32px] font-semibold tracking-[-0.02em]">Settings</h1>
        <p className="text-sec text-sm mt-2">Provider configuration status. Secrets stay server-side — never exposed to the browser.</p>
        {!cfg ? <div className="skel h-40 mt-6" /> : cfg.offline ? (
          <div className="card p-6 mt-6 text-sm text-neg">Backend unreachable at {String(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")}. Start it with <code>uvicorn app.main:app</code> in <code>backend/</code>.</div>
        ) : (
          <div className="space-y-3 mt-6">
            <div className="card p-5">
              <div className="label mb-2">LLM provider — {cfg.llm?.configured ? "configured" : "deterministic engine (no key needed)"}</div>
              <p className="text-sm text-sec">Provider: <span className="text-pri num">{cfg.llm?.provider}</span> · Model: <span className="text-pri num">{cfg.llm?.model}</span></p>
              <p className="text-[13px] text-ter mt-1">{cfg.llm?.role}. Set <code>LLM_PROVIDER=openai_compatible</code> + <code>LLM_BASE_URL / LLM_API_KEY / LLM_MODEL</code> in <code>backend/.env</code> to enable LLM explanations.</p>
            </div>
            <div className="card p-5">
              <div className="label mb-2">Web search — {cfg.search?.provider}{cfg.search?.configured ? " · active" : " · not configured"}</div>
              <p className="text-[13px] text-ter">Built-in keyless provider works out of the box. For higher recall set <code>SEARCH_PROVIDER=serper|tavily</code> with the matching key in <code>backend/.env</code>.</p>
            </div>
            <div className="card p-5">
              <div className="label mb-2">Fetch policy</div>
              <p className="text-sm text-sec num">timeout {cfg.fetch?.timeout_s}s · max {cfg.fetch?.max_pages} pages per investigation · SSRF-guarded · 1 req/s politeness</p>
            </div>
            <div className="card p-5">
              <div className="label mb-2">Tracks</div>
              <ul className="text-sm text-sec space-y-1">{Object.entries(cfg.tracks ?? {}).map(([k, v]) => <li key={k}>Track {k} — {String(v)}</li>)}</ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
