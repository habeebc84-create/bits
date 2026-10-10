"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

export function MetricChart({ title, data, source, kind = "line" }: {
  title: string; data: { period: string; value: number }[]; source: string; kind?: "line" | "bar";
}) {
  if (!data.length) return null;
  return (
    <div className="card p-5">
      <div className="label mb-1">{title}</div>
      <div className="h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          {kind === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid stroke="#1E2A3B" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="period" tick={{ fill: "#5C6B7F", fontSize: 11 }} axisLine={{ stroke: "#1E2A3B" }} tickLine={false} />
              <YAxis tick={{ fill: "#5C6B7F", fontSize: 11 }} axisLine={false} tickLine={false} width={64} />
              <Tooltip contentStyle={{ background: "#0F1623", border: "1px solid #1E2A3B", fontSize: 12 }} labelStyle={{ color: "#8B9CB3" }} />
              <Line type="monotone" dataKey="value" stroke="#3EC9D6" strokeWidth={2} dot={{ r: 3, fill: "#3EC9D6" }} />
            </LineChart>
          ) : (
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid stroke="#1E2A3B" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="period" tick={{ fill: "#5C6B7F", fontSize: 11 }} axisLine={{ stroke: "#1E2A3B" }} tickLine={false} />
              <YAxis tick={{ fill: "#5C6B7F", fontSize: 11 }} axisLine={false} tickLine={false} width={64} />
              <Tooltip contentStyle={{ background: "#0F1623", border: "1px solid #1E2A3B", fontSize: 12 }} labelStyle={{ color: "#8B9CB3" }} />
              <Bar dataKey="value" fill="#3EC9D6" opacity={0.75} radius={[3, 3, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <div className="text-[11px] text-ter mt-2">Source: {source} · validated data only · gaps shown honestly</div>
    </div>
  );
}

export function StageBar({ stages, index, status }: { stages: string[]; index: number; status: string }) {
  return (
    <ol className="flex flex-wrap gap-1.5">
      {stages.map((s, i) => {
        const done = i < index || status === "completed";
        const cur = i === index && status === "running";
        return (
          <li key={s} className={`text-[11px] px-2.5 py-1 rounded border font-medium uppercase tracking-wide
            ${done ? "text-pos border-pos/30 bg-pos/5" : cur ? "text-accent border-accent/50 bg-accent/10" : "text-ter border-line bg-surf1"}`}>
            {done ? "✓ " : ""}{s}
          </li>
        );
      })}
    </ol>
  );
}
