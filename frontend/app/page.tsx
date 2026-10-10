import Link from "next/link";
import Nav from "@/components/Nav";
import { Crosshair, Network, Calculator, Swords, FileCheck2, ArrowRight } from "lucide-react";

const CAPS = [
  { icon: Crosshair, t: "Autonomous discovery", d: "Plans its own research questions from available evidence." },
  { icon: Network, t: "Cross-source research", d: "Filings, reports, transcripts, peers — triangulated." },
  { icon: Calculator, t: "Financial calculations", d: "Deterministic finlib arithmetic with full provenance." },
  { icon: Swords, t: "Adversarial testing", d: "Steel-mans the strongest alternative before concluding." },
  { icon: FileCheck2, t: "Auditable evidence", d: "Every number clickable back to passage and document." },
];

const STEPS = ["Investigate", "Retrieve", "Calculate", "Hypothesize", "Challenge", "Prove"];

export default function Home() {
  return (
    <div>
      <Nav />
      <main className="max-w-[1240px] mx-auto px-6">
        <section className="py-20 md:py-28 max-w-3xl relative">
          <svg className="absolute -right-40 top-6 w-[420px] opacity-[0.16] pointer-events-none hidden lg:block" viewBox="0 0 400 300" fill="none" aria-hidden>
            {[[60,60],[160,40],[260,80],[120,150],[220,160],[320,140],[90,230],[200,240],[310,230]].map(([x,y],i)=>(
              <g key={i}><circle cx={x} cy={y} r="4" fill="#3EC9D6"/>{i<8 && <line x1={x} y1={y} x2={[160,260,120,220,320,90,200,310,60][i]} y2={[40,80,150,160,140,230,240,230,60][i]} stroke="#3EC9D6" strokeWidth="1"/>}</g>
            ))}
          </svg>
          <p className="label mb-4">Autonomous Financial Intelligence · NSE / BSE · INR</p>
          <h1 className="text-[34px] md:text-[42px] leading-[1.1] font-semibold tracking-[-0.02em]">
            Find the financial story hiding in plain sight.
          </h1>
          <p className="text-sec text-[15px] leading-[1.55] mt-5 max-w-2xl">
            An autonomous financial research agent that connects public filings, financial data, industry
            developments, and competitor signals to discover evidence-backed insights conventional dashboards can miss.
          </p>
          <div className="flex gap-3 mt-8">
            <Link href="/research/new" className="bg-accent text-ink font-semibold text-sm px-5 py-2.5 rounded-md hover:brightness-110 inline-flex items-center gap-2">
              Start an Investigation <ArrowRight size={15} />
            </Link>
            <Link href="/methodology" className="border border-line text-pri text-sm px-5 py-2.5 rounded-md hover:bg-surf2">
              Explore the Methodology
            </Link>
          </div>
        </section>

        <section className="grid md:grid-cols-5 gap-3 pb-16">
          {CAPS.map((c) => (
            <div key={c.t} className="card p-4">
              <c.icon size={17} className="text-accent mb-2.5" />
              <div className="text-sm font-semibold">{c.t}</div>
              <div className="text-[13px] text-sec mt-1 leading-relaxed">{c.d}</div>
            </div>
          ))}
        </section>

        <section className="card p-6 md:p-8 mb-16">
          <div className="flex items-center gap-2 mb-3">
            <span className="label">Example discovery</span>
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border border-warn/40 text-warn bg-warn/10">Illustrative · fictional</span>
          </div>
          <h2 className="text-[20px] font-semibold tracking-tight">“Profit grew 34% while cash conversion stretched 21 days — earnings or accrual?”</h2>
          <p className="text-sec text-sm mt-2 max-w-3xl">A typical SIGNAL HUNTER X output cross-checks PAT growth against debtor days, inventory, peer movement, and management commentary — then argues against itself before assigning an evidence grade.</p>
          <div className="grid md:grid-cols-3 gap-3 mt-5">
            {[["PAT growth (FY22→FY24)", "+34.2%", "audited P&L"], ["Cash conversion cycle", "+21 days", "balance sheet"], ["Evidence strength", "Moderate", "2 independent lines"]].map(([k, v, s]) => (
              <div key={k} className="bg-surf2 border border-line rounded-md p-4">
                <div className="label">{k}</div>
                <div className="text-xl font-semibold num text-accent mt-1">{v}</div>
                <div className="text-[11px] text-ter mt-1">{s}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="pb-16">
          <h2 className="text-[19px] font-semibold mb-5">How it investigates</h2>
          <div className="grid md:grid-cols-6 gap-3">
            {STEPS.map((s, i) => (
              <div key={s} className="card p-4">
                <div className="text-accent font-semibold text-sm num">0{i + 1}</div>
                <div className="text-sm font-semibold mt-1">{s}</div>
              </div>
            ))}
          </div>
          <p className="text-sec text-sm mt-4 max-w-3xl">Investigate → Retrieve → Calculate → Hypothesize → Challenge → Prove. Every stage persists intermediate results; the UI only shows what the backend actually reports. <Link href="/methodology" className="text-accent">Full methodology →</Link></p>
        </section>
      </main>
      <footer className="border-t border-line/70">
        <div className="max-w-[1240px] mx-auto px-6 py-10 text-[13px] text-sec flex flex-col md:flex-row gap-3 md:items-center">
          <span>ATMOS 2026 · BITS Pilani, Hyderabad Campus — Finding the Next Signal</span>
          <span className="md:ml-auto flex gap-5">
            <Link href="/methodology" className="hover:text-pri">Methodology</Link>
            <Link href="/history" className="hover:text-pri">History</Link>
            <Link href="/settings" className="hover:text-pri">Settings</Link>
          </span>
          <span className="text-ter text-[12px]">Research tool — not investment advice. Verify against primary sources.</span>
        </div>
      </footer>
    </div>
  );
}
