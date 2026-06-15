import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { useApi } from "../useApi";

export default function Dashboard() {
  const summary = useApi(api.summary);
  const coverage = useApi(api.coverage);

  if (summary.loading || coverage.loading)
    return <div className="loading">Loading compliance posture…</div>;
  if (summary.error) return <div className="error">API error: {summary.error}</div>;

  const s = summary.data!;
  const cov = coverage.data ?? [];

  // How many controls satisfy each framework — the "buy-in" chart.
  const counts: Record<string, number> = {};
  for (const c of cov) {
    for (const fw of c.frameworks_covered) counts[fw] = (counts[fw] ?? 0) + 1;
  }
  const chartData = Object.entries(counts).map(([name, controls]) => ({
    name,
    controls,
  }));

  return (
    <>
      <h1>Compliance Posture</h1>
      <p className="subtitle">
        One control, many frameworks. This is your single source of truth.
      </p>

      <div className="cards">
        <Stat value={s.frameworks} label="Frameworks" />
        <Stat value={s.common_controls} label="Common Controls" />
        <Stat value={s.requirements} label="Mapped Requirements" />
        <Stat value={s.mappings} label="Control ↔ Requirement Mappings" />
      </div>

      <div className="panel">
        <h2>Controls satisfying each framework</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2c3a4f" />
            <XAxis dataKey="name" stroke="#8b9bb0" />
            <YAxis stroke="#8b9bb0" allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: "#1a2230",
                border: "1px solid #2c3a4f",
                borderRadius: 8,
                color: "#e6edf3",
              }}
            />
            <Bar dataKey="controls" fill="#4f8cff" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="card">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}
