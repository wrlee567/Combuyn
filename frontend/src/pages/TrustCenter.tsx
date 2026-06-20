import { api } from "../api";
import { badgeClass } from "../badge";
import { useApi } from "../useApi";

export default function TrustCenter() {
  const { data, loading, error } = useApi(api.trustCenter);

  if (loading) return <div className="loading">Loading Trust Center...</div>;
  if (error) return <div className="error">API error: {error}</div>;

  const trust = data!;

  return (
    <>
      <h1>Trust Center</h1>
      <p className="subtitle">
        Public security, privacy, compliance, and AI transparency posture.
      </p>

      <div className="panel">
        <h2>Continuous Monitoring</h2>
        <div className="trust-grid">
          {trust.frameworks.map((framework) => (
            <div className="trust-status" key={framework.id}>
              <div className="framework-name">{framework.framework}</div>
              <div className="progress-bar">
                <div style={{ width: `${framework.coverage_percent}%` }} />
              </div>
              <div className="trust-meta">
                <span className={badgeClass(framework.status)}>{framework.status}</span>
                <span>{framework.coverage_percent}% coverage</span>
                <span>{framework.monitored_controls} controls</span>
              </div>
              <p>{framework.public_summary}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>AI Transparency</h2>
        <table>
          <thead>
            <tr>
              <th>AI System</th>
              <th>EU AI Act Flags</th>
              <th>Notice</th>
              <th>Public Summary</th>
            </tr>
          </thead>
          <tbody>
            {trust.ai_transparency.map((item) => (
              <tr key={item.id}>
                <td>
                  <div className="control-key">{item.system_name}</div>
                </td>
                <td>
                  {item.direct_user_interaction && (
                    <span className="badge generic">direct user interaction</span>
                  )}
                  {item.biometric_data && <span className="badge amber">biometric data</span>}
                  {item.synthetic_content && (
                    <span className="badge nist">synthetic content</span>
                  )}
                  {item.deepfake_generation && (
                    <span className="badge red">deepfake generation</span>
                  )}
                  {!item.direct_user_interaction &&
                    !item.biometric_data &&
                    !item.synthetic_content &&
                    !item.deepfake_generation && (
                      <span className="badge green">no public transparency trigger</span>
                    )}
                </td>
                <td>
                  <span
                    className={
                      item.eu_transparency_notice === "required"
                        ? "badge amber"
                        : "badge green"
                    }
                  >
                    {item.eu_transparency_notice}
                  </span>
                </td>
                <td>{item.public_summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>Document Requests</h2>
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Access</th>
              <th>NDA</th>
              <th>Workflow</th>
            </tr>
          </thead>
          <tbody>
            {trust.documents.map((document) => (
              <tr key={document.id}>
                <td>
                  <div className="control-key">{document.document_name}</div>
                  <div className="domain">{document.sensitivity}</div>
                </td>
                <td>
                  <span className="badge generic">{document.fulfillment_status}</span>
                </td>
                <td>
                  <span className={document.nda_required ? "badge amber" : "badge green"}>
                    {document.nda_status}
                  </span>
                </td>
                <td>{document.request_workflow}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
