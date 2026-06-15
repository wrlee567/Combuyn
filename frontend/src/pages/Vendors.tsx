import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { humanize, riskClass } from "../badge";
import { useApi } from "../useApi";

export default function Vendors() {
  const { data, loading, error } = useApi(api.vendors);
  const navigate = useNavigate();

  if (loading) return <div className="loading">Loading vendors…</div>;
  if (error) return <div className="error">API error: {error}</div>;

  const vendors = data ?? [];

  return (
    <>
      <div className="row">
        <div>
          <h1>Third-Party Vendors</h1>
          <p className="subtitle" style={{ margin: 0 }}>
            Inherent risk is scored at intake, before any controls are applied.
          </p>
        </div>
        <a className="btn" href="/vendors/new">
          + Add Vendor
        </a>
      </div>

      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Vendor</th>
              <th>Industry</th>
              <th>Lifecycle</th>
              <th>Inherent Risk</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map((v) => (
              <tr
                key={v.id}
                className="clickable"
                onClick={() => navigate(`/vendors/${v.id}`)}
              >
                <td>
                  <div style={{ fontWeight: 600 }}>{v.name}</div>
                </td>
                <td className="muted">{humanize(v.industry)}</td>
                <td>
                  <span className="badge generic">
                    {humanize(v.lifecycle_status)}
                  </span>
                </td>
                <td>
                  <span className={riskClass(v.inherent_risk_tier)}>
                    {v.inherent_risk_tier}
                  </span>{" "}
                  <span className="score-bar">
                    <span style={{ width: `${v.inherent_risk_score}%` }} />
                  </span>{" "}
                  <span className="muted">{v.inherent_risk_score}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {vendors.length === 0 && (
          <p className="muted">No vendors yet. Add your first one.</p>
        )}
      </div>
    </>
  );
}
