import Nav from "@/components/Nav";

const RULES = [
  ["Reported facts", "Verbatim passages with document, page/section, period, units. Never paraphrased into new numbers."],
  ["Calculated values", "finlib-v1 only (Python/pandas). Formula, inputs, evidence IDs, and code version stored per metric. The LLM explains — never computes."],
  ["Standalone vs consolidated", "Series are scope-tagged; mixed-scope comparisons are refused."],
  ["Period comparability", "FY↔FY and same-quarter only. TTM never compared against audited FY."],
  ["Independence", "Repeated coverage of one announcement counts once. Publisher-level dedup + content-hash dedup."],
  ["Contradiction first", "A dedicated contrary-evidence search + steel-man alternative run before any conclusion."],
  ["Strength grades", "Strong needs ≥3 independent lines + reproducible calcs + tested counterargument. Otherwise Moderate/Weak — never inflated."],
  ["Falsifiability", "Every discovery names the future filing/metric/threshold that would overturn it."],
  ["Honest inconclusive", "Below-threshold evidence returns “Insufficient evidence for a defensible discovery” — never a fabricated signal."],
];

export default function Methodology() {
  return (
    <div>
      <Nav active="/methodology" />
      <main className="max-w-[1240px] mx-auto px-6 py-12 max-w-3xl">
        <p className="label mb-3">Research methodology · calculations · evidence standards</p>
        <h1 className="text-[32px] font-semibold tracking-[-0.02em]">How SIGNAL HUNTER X earns trust</h1>
        <p className="text-sec text-[15px] mt-3 leading-relaxed">Eleven persisted stages — resolve, plan, discover, extract, financials, patterns, hypothesize, triangulate, adversarial, assess, report. Intermediate results live in the database, so any interrupted job can be diagnosed or resumed, and any claim can be traced to passage, document, and arithmetic.</p>
        <div className="space-y-3 mt-8">
          {RULES.map(([t, d], i) => (
            <div key={t} className="card p-5 flex gap-4">
              <span className="text-accent font-semibold num text-sm">0{i + 1}</span>
              <div><div className="text-[15px] font-semibold">{t}</div><div className="text-sm text-sec mt-1 leading-relaxed">{d}</div></div>
            </div>
          ))}
        </div>
        <div className="card p-5 mt-6 text-sm text-sec">
          <span className="label">Data limitations</span>
          <p className="mt-2">Public sources only (NSE/BSE filings, annual reports, results, transcripts where public, reputable journalism, Screener.in aggregates). Paywalled, API-gated, and non-public data are out of scope. Fetches respect robots policies, rate limits, and SSRF guards; failures are recorded as coverage gaps, never silently converted into success.</p>
        </div>
      </main>
    </div>
  );
}
