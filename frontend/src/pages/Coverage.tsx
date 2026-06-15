import { api } from "../api";
import { badgeClass } from "../badge";
import { useApi } from "../useApi";

export default function Coverage() {
  const { data, loading, error } = useApi(api.coverage);

  if (loading) return <div className="loading">Loading control coverage…</div>;
  if (error) return <div className="error">API error: {error}</div>;

  return (
    <>
      <h1>Control Coverage Matrix</h1>
      <p className="subtitle">
        Each common control, and every framework requirement it satisfies —
        implement once, comply many.
      </p>
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Common Control</th>
              <th>Frameworks</th>
              <th>Satisfies Requirements</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((c) => (
              <tr key={c.id}>
                <td>
                  <div className="control-key">{c.key}</div>
                  <div>{c.name}</div>
                  <div className="domain">{c.domain}</div>
                </td>
                <td>
                  {c.frameworks_covered.map((fw) => (
                    <span key={fw} className={badgeClass(fw)}>
                      {fw}
                    </span>
                  ))}
                </td>
                <td>
                  {c.requirements.map((r) => (
                    <div key={`${r.framework_key}-${r.citation}`}>
                      <span className={badgeClass(r.framework_key)}>
                        {r.framework_name}
                      </span>{" "}
                      <span className="cite">{r.citation}</span>{" "}
                      <span className="muted">{r.title}</span>
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
