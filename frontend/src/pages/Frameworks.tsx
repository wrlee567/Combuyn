import { api } from "../api";
import { useApi } from "../useApi";

export default function Frameworks() {
  const { data, loading, error } = useApi(api.frameworks);

  if (loading) return <div className="loading">Loading frameworks…</div>;
  if (error) return <div className="error">API error: {error}</div>;

  return (
    <>
      <h1>Frameworks</h1>
      <p className="subtitle">
        Regulatory standards Combuyn maps your controls against.
      </p>
      <div className="panel">
        {(data ?? []).map((fw) => (
          <div className="framework-card" key={fw.id}>
            <div>
              <div className="framework-name">
                {fw.name} <span className="muted">{fw.version}</span>
              </div>
              <div className="framework-meta">
                {fw.authority} · {fw.description}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="value" style={{ fontSize: 24 }}>
                {fw.requirement_count}
              </div>
              <div className="domain">requirements</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
