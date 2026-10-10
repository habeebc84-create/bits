export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body.slice(0, 300) || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type CompanyHit = {
  canonical_name: string; ticker: string; exchange: string;
  sector: string; industry: string; website: string; track: string;
};

export const api = {
  health: () => fetch(`${API}/api/health`).then(j),
  config: () => fetch(`${API}/api/config`).then(j),
  searchCompanies: (q: string) =>
    fetch(`${API}/api/companies/search?q=${encodeURIComponent(q)}`).then(j<{ results: CompanyHit[] }>),
  createResearch: (body: object) =>
    fetch(`${API}/api/research`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(j<{ id: string }>),
  research: (id: string) => fetch(`${API}/api/research/${id}`).then(j<any>),
  cancel: (id: string) => fetch(`${API}/api/research/${id}/cancel`, { method: "POST" }).then(j<any>),
  retry: (id: string) => fetch(`${API}/api/research/${id}/retry`, { method: "POST" }).then(j<any>),
  discovery: (id: string) => fetch(`${API}/api/discoveries/${id}`).then(j<any>),
  evidence: (id: string) => fetch(`${API}/api/discoveries/${id}/evidence`).then(j<any>),
  history: (p: Record<string, string> = {}) =>
    fetch(`${API}/api/history?` + new URLSearchParams(p)).then(j<{ total: number; items: any[] }>),
  exportUrl: (id: string) => `${API}/api/discoveries/${id}/export`,
  eventsUrl: (id: string) => `${API}/api/research/${id}/events`,
};

export const TRACKS: Record<string, string> = {
  A: "Banking, NBFCs & Financial Services",
  B: "Energy, Power & Renewables",
  C: "Consumer, FMCG & Retail",
  D: "Pharma & Healthcare",
};

export function strengthColor(s: string) {
  return s === "Strong" ? "text-pos border-pos/40 bg-pos/10"
    : s === "Moderate" ? "text-warn border-warn/40 bg-warn/10"
    : "text-neg border-neg/40 bg-neg/10";
}
