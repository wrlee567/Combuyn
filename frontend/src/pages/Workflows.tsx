import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  api,
  type WorkflowDefinitionSummary,
  type WorkflowInstanceSummary,
} from "../api";
import { humanize } from "../badge";

function statusClass(status: string): string {
  return `badge wf-${status}`;
}

export default function Workflows() {
  const navigate = useNavigate();
  const [defs, setDefs] = useState<WorkflowDefinitionSummary[]>([]);
  const [instances, setInstances] = useState<WorkflowInstanceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  function load() {
    Promise.all([api.workflowDefinitions(), api.workflowInstances()])
      .then(([d, i]) => {
        setDefs(d);
        setInstances(i);
      })
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function launch(def: WorkflowDefinitionSummary) {
    const subject = window.prompt(`Subject for new "${def.name}" run:`);
    if (!subject) return;
    setBusyKey(def.key);
    try {
      const created = await api.createWorkflowInstance({
        definition_key: def.key,
        subject,
      });
      navigate(`/workflows/${created.id}`);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusyKey(null);
    }
  }

  if (loading) return <div className="loading">Loading workflows…</div>;

  const defName = (id: string) =>
    defs.find((d) => d.id === id)?.name ?? "Workflow";

  return (
    <>
      <h1>Workflow Orchestration</h1>
      <p className="subtitle" style={{ marginTop: 0 }}>
        Durable state machines: every transition is persisted, can be rolled back
        via Saga compensation, and notifies Slack.
      </p>

      {error && <div className="notice error">{error}</div>}

      <div className="panel">
        <h2>Blueprints</h2>
        <div className="wf-def-grid">
          {defs.map((d) => (
            <div className="wf-def-card" key={d.id}>
              <div style={{ fontWeight: 600 }}>{d.name}</div>
              <p className="muted" style={{ flex: 1 }}>
                {d.description}
              </p>
              <button
                className="btn"
                disabled={busyKey === d.key}
                onClick={() => launch(d)}
              >
                {busyKey === d.key ? "Starting…" : "+ Launch run"}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>Running &amp; Completed</h2>
        <table>
          <thead>
            <tr>
              <th>Subject</th>
              <th>Workflow</th>
              <th>Current state</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {instances.map((i) => (
              <tr
                key={i.id}
                className="clickable"
                onClick={() => navigate(`/workflows/${i.id}`)}
              >
                <td style={{ fontWeight: 600 }}>{i.subject}</td>
                <td className="muted">{defName(i.definition_id)}</td>
                <td>
                  <span className="badge generic">
                    {humanize(i.current_state)}
                  </span>
                </td>
                <td>
                  <span className={statusClass(i.status)}>
                    {humanize(i.status)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {instances.length === 0 && (
          <p className="muted">No workflow runs yet. Launch one above.</p>
        )}
      </div>
    </>
  );
}
