import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type Blueprint, type WorkflowInstanceDetail } from "../api";
import { humanize } from "../badge";

// Assign each state a column index = shortest forward distance from the initial
// state, so the blueprint renders left-to-right like a flow diagram.
function levelStates(bp: Blueprint): string[][] {
  const level: Record<string, number> = { [bp.initial]: 0 };
  const queue = [bp.initial];
  while (queue.length) {
    const s = queue.shift()!;
    for (const t of bp.transitions) {
      if (t.from === s && level[t.to] === undefined) {
        level[t.to] = level[s] + 1;
        queue.push(t.to);
      }
    }
  }
  const maxLevel = Math.max(0, ...Object.values(level));
  const cols: string[][] = Array.from({ length: maxLevel + 1 }, () => []);
  for (const st of bp.states) cols[level[st.id] ?? maxLevel].push(st.id);
  return cols;
}

export default function WorkflowDetail() {
  const { id = "" } = useParams();
  const [inst, setInst] = useState<WorkflowInstanceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .workflowInstance(id)
      .then(setInst)
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoading(false));
  }, [id]);

  async function run(fn: () => Promise<WorkflowInstanceDetail>) {
    setBusy(true);
    setError(null);
    try {
      setInst(await fn());
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="loading">Loading workflow…</div>;
  if (error || !inst)
    return (
      <>
        <a className="back-link" href="/workflows">
          ← Workflows
        </a>
        <div className="notice error">
          Couldn't load this run ({error}). Workflow detail needs the live
          backend — connect the API to drive it.
        </div>
      </>
    );

  const bp = inst.blueprint;
  const cols = levelStates(bp);
  const labelOf = (sid: string) =>
    bp.states.find((s) => s.id === sid)?.label ?? humanize(sid);
  const isTerminal = (sid: string) =>
    bp.states.find((s) => s.id === sid)?.type === "end";

  return (
    <>
      <a className="back-link" href="/workflows">
        ← Workflows
      </a>
      <div className="row">
        <h1 style={{ margin: 0 }}>{inst.subject}</h1>
        <span className={`badge wf-${inst.status}`}>{humanize(inst.status)}</span>
      </div>
      <p className="subtitle" style={{ marginTop: 4 }}>
        {inst.definition_name} · currently{" "}
        <strong>{labelOf(inst.current_state)}</strong>
      </p>

      {error && <div className="notice error">{error}</div>}

      <div className="panel">
        <h2>Blueprint</h2>
        <div className="wf-graph">
          {cols.map((col, ci) => (
            <div className="wf-col" key={ci}>
              {col.map((sid) => {
                const cls = [
                  "wf-node",
                  sid === inst.current_state ? "active" : "",
                  isTerminal(sid) ? "terminal" : "",
                ]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <div className={cls} key={sid}>
                    {labelOf(sid)}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>Actions</h2>
        {inst.status === "running" ? (
          <div className="wf-actions">
            {inst.available_actions.map((a) => (
              <button
                key={a.action}
                className="btn"
                disabled={busy}
                onClick={() => run(() => api.advanceWorkflow(id, a.action))}
              >
                {humanize(a.action)} → {labelOf(a.target)}
              </button>
            ))}
            <button
              className="btn ghost"
              disabled={busy}
              onClick={() => run(() => api.compensateWorkflow(id))}
            >
              ↩ Roll back (Saga)
            </button>
          </div>
        ) : (
          <p className="muted">
            This run is {humanize(inst.status)} — no further actions.
          </p>
        )}
      </div>

      <div className="panel">
        <h2>Event Log</h2>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Kind</th>
              <th>Action</th>
              <th>Transition</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {inst.events.map((e) => (
              <tr key={e.sequence}>
                <td className="muted">{e.sequence}</td>
                <td>
                  <span className={`badge wf-evt-${e.kind}`}>{e.kind}</span>
                </td>
                <td>{e.action ? humanize(e.action) : "—"}</td>
                <td className="muted">
                  {e.from_state ? labelOf(e.from_state) : "∅"} →{" "}
                  {labelOf(e.to_state)}
                </td>
                <td className="muted">{e.note || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
