import { Link, useParams } from "react-router-dom";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type AIEvidenceItem,
  type AILaunchGate,
  type EvidencePatch,
} from "../api";
import { badgeClass } from "../badge";

const evidenceStatuses: EvidencePatch["status"][] = [
  "missing",
  "provided",
  "accepted",
  "rejected",
];

export default function AILaunchGate() {
  const { id } = useParams();
  const [gate, setGate] = useState<AILaunchGate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [decisionSummary, setDecisionSummary] = useState("");
  const [nextReviewDate, setNextReviewDate] = useState("");

  const loadGate = useCallback(() => {
    if (!id) return Promise.resolve();
    setLoading(true);
    setError(null);
    return api
      .aiLaunchGate(id)
      .then((data) => {
        setGate(data);
        setDecisionSummary(data.governance_review?.decision_summary ?? "");
        setNextReviewDate(data.governance_review?.next_review_date ?? "");
      })
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    void loadGate();
  }, [loadGate]);

  const canApprove =
    gate?.governance_review !== null &&
    gate?.readiness.evidence_missing === 0 &&
    gate?.readiness.evidence_rejected === 0;

  const stateLabel = gate ? gate.readiness.state.replace("_", " ") : "";

  async function saveEvidence(itemId: string, body: EvidencePatch) {
    setSaving(itemId);
    setError(null);
    try {
      await api.updateAIEvidence(itemId, body);
      await loadGate();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSaving(null);
    }
  }

  async function saveDecision(status: string) {
    if (!gate?.governance_review) return;
    setSaving("decision");
    setError(null);
    try {
      await api.updateAIReviewDecision(gate.governance_review.id, {
        status,
        decision_summary: decisionSummary,
        next_review_date: nextReviewDate || null,
      });
      await loadGate();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <div className="loading">Loading launch gate...</div>;
  if (error && !gate) return <div className="error">API error: {error}</div>;
  if (!gate) return <div className="empty-state">No launch gate found.</div>;

  return (
    <>
      <Link className="back-link" to="/ai-governance">
        Back to AI Governance
      </Link>

      <div className="launch-header">
        <div>
          <h1>{gate.system.name}</h1>
          <p className="subtitle">{gate.system.business_purpose}</p>
        </div>
        <div className="readiness-dial">
          <div className="readiness-score">{gate.readiness.score}</div>
          <span className={stateBadge(gate.readiness.state)}>{stateLabel}</span>
        </div>
      </div>

      {error ? <div className="notice error">{error}</div> : null}

      <div className="launch-grid">
        <section className="panel launch-section">
          <div className="panel-heading">
            <div>
              <h2>Classification</h2>
              <p className="panel-subtitle">
                {gate.latest_classification?.regulatory_scope ?? "Review required"}
              </p>
            </div>
            <span className={riskBadge(gate.latest_classification?.risk_tier)}>
              {gate.latest_classification?.risk_tier ?? "Unclassified"}
            </span>
          </div>
          <div className="kv compact">
            <div className="k">Owner</div>
            <div>{gate.system.owner}</div>
            <div className="k">Role</div>
            <div>{gate.system.regulatory_role}</div>
            <div className="k">Lifecycle</div>
            <div>{gate.system.lifecycle_stage}</div>
            <div className="k">Deployment</div>
            <div>{gate.system.deployment_environment}</div>
          </div>
          <p className="launch-copy">
            {gate.latest_classification?.rationale ?? "No classification rationale recorded."}
          </p>
        </section>

        <section className="panel launch-section">
          <div className="panel-heading">
            <div>
              <h2>Obligations</h2>
              <p className="panel-subtitle">
                {gate.readiness.tasks_complete} of {gate.readiness.tasks_total} complete
              </p>
            </div>
            <span className="badge generic">{gate.tasks.length} tasks</span>
          </div>
          <div className="task-list">
            {gate.tasks.length ? (
              gate.tasks.map((task) => (
                <div className="task-row" key={task.id}>
                  <div>
                    <div>{task.obligation}</div>
                    <div className="domain">
                      {task.framework} - {task.owner_role} - due +{task.due_offset_days}d
                    </div>
                  </div>
                  <span className={badgeClass(task.status)}>{task.status}</span>
                </div>
              ))
            ) : (
              <div className="empty-state small">No obligations generated.</div>
            )}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Evidence Readiness</h2>
            <p className="panel-subtitle">
              {gate.readiness.evidence_ready} of {gate.readiness.evidence_total} ready
            </p>
          </div>
          <div className="launch-badges">
            <span className="badge amber">{gate.readiness.evidence_missing} missing</span>
            <span className="badge red">{gate.readiness.evidence_rejected} rejected</span>
          </div>
        </div>
        <div className="progress-bar evidence-bar">
          <div style={{ width: `${evidencePercent(gate)}%` }} />
        </div>
        <div className="evidence-edit-list">
          {gate.evidence_items.map((item) => (
            <EvidenceEditor
              item={item}
              key={item.id}
              saving={saving === item.id}
              onSave={(body) => saveEvidence(item.id, body)}
            />
          ))}
        </div>
      </section>

      <div className="launch-grid">
        <section className="panel launch-section">
          <div className="panel-heading">
            <div>
              <h2>Launch Decision</h2>
              <p className="panel-subtitle">
                {gate.governance_review?.reviewer ?? "Reviewer unassigned"}
              </p>
            </div>
            <span className={stateBadge(gate.readiness.state)}>{stateLabel}</span>
          </div>

          {gate.governance_review ? (
            <>
              <div className="review-meta">
                <span className={badgeClass(gate.governance_review.status)}>
                  {gate.governance_review.status}
                </span>
                <span className={riskBadge(gate.governance_review.risk_level)}>
                  {gate.governance_review.risk_level}
                </span>
                <span className="badge generic">
                  {gate.governance_review.next_review_date
                    ? formatDate(gate.governance_review.next_review_date)
                    : "unscheduled"}
                </span>
              </div>
              <div className="decision-form">
                <label>
                  Summary
                  <textarea
                    value={decisionSummary}
                    onChange={(event) => setDecisionSummary(event.target.value)}
                    rows={4}
                  />
                </label>
                <label>
                  Next review
                  <input
                    type="date"
                    value={nextReviewDate}
                    onChange={(event) => setNextReviewDate(event.target.value)}
                  />
                </label>
                {gate.readiness.approval_blockers.length ? (
                  <div className="blocker-list">
                    {gate.readiness.approval_blockers.map((blocker) => (
                      <div key={blocker}>{blocker}</div>
                    ))}
                  </div>
                ) : null}
                <div className="wf-actions">
                  <button
                    className="btn secondary"
                    disabled={saving === "decision"}
                    onClick={() => saveDecision("under review")}
                  >
                    Save Review
                  </button>
                  <button
                    className="btn"
                    disabled={!canApprove || saving === "decision"}
                    onClick={() => saveDecision("approved")}
                  >
                    Approve
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state small">No governance review found.</div>
          )}
        </section>

        <section className="panel launch-section">
          <div className="panel-heading">
            <div>
              <h2>Trust Center</h2>
              <p className="panel-subtitle">
                {gate.trust_center_transparency?.eu_transparency_notice ?? "not synced"}
              </p>
            </div>
            <span
              className={
                gate.trust_center_transparency?.eu_transparency_notice === "required"
                  ? "badge amber"
                  : "badge green"
              }
            >
              transparency
            </span>
          </div>
          {gate.trust_center_transparency ? (
            <>
              <p className="launch-copy">{gate.trust_center_transparency.public_summary}</p>
              <div className="trust-flags">
                <Flag
                  label="Direct interaction"
                  active={gate.trust_center_transparency.direct_user_interaction}
                />
                <Flag
                  label="Biometric data"
                  active={gate.trust_center_transparency.biometric_data}
                />
                <Flag
                  label="Synthetic content"
                  active={gate.trust_center_transparency.synthetic_content}
                />
                <Flag
                  label="Deepfake"
                  active={gate.trust_center_transparency.deepfake_generation}
                />
              </div>
            </>
          ) : (
            <div className="empty-state small">No transparency row found.</div>
          )}
        </section>
      </div>
    </>
  );
}

function EvidenceEditor({
  item,
  saving,
  onSave,
}: {
  item: AIEvidenceItem;
  saving: boolean;
  onSave: (body: EvidencePatch) => void;
}) {
  const [status, setStatus] = useState<EvidencePatch["status"]>(
    item.status as EvidencePatch["status"],
  );
  const [evidenceUri, setEvidenceUri] = useState(item.evidence_uri);
  const [notes, setNotes] = useState(item.notes);

  const dirty = useMemo(
    () =>
      status !== item.status ||
      evidenceUri !== item.evidence_uri ||
      notes !== item.notes,
    [evidenceUri, item.evidence_uri, item.notes, item.status, notes, status],
  );

  return (
    <div className="evidence-edit-row">
      <div className="evidence-edit-main">
        <div className="control-key">{item.requirement}</div>
        <div>{item.title}</div>
        <div className="domain">
          {item.evidence_type} - {item.owner}
        </div>
      </div>
      <div className="evidence-controls">
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value as EvidencePatch["status"])}
        >
          {evidenceStatuses.map((candidate) => (
            <option value={candidate} key={candidate}>
              {candidate}
            </option>
          ))}
        </select>
        <input
          value={evidenceUri}
          onChange={(event) => setEvidenceUri(event.target.value)}
          placeholder="Evidence URI"
        />
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={2}
          placeholder="Notes"
        />
        <button
          className="btn secondary"
          disabled={!dirty || saving}
          onClick={() => onSave({ status, evidence_uri: evidenceUri, notes })}
        >
          Save
        </button>
      </div>
    </div>
  );
}

function Flag({ label, active }: { label: string; active: boolean }) {
  return <span className={active ? "badge amber" : "badge generic"}>{label}</span>;
}

function evidencePercent(gate: AILaunchGate) {
  if (!gate.readiness.evidence_total) return 0;
  return Math.round(
    (gate.readiness.evidence_ready / gate.readiness.evidence_total) * 100,
  );
}

function riskBadge(value = "") {
  if (value.includes("High") || value === "high") return "badge amber";
  if (value.includes("GPAI")) return "badge nist";
  if (value.includes("Limited") || value === "medium") return "badge generic";
  if (value.includes("Minimal") || value === "low") return "badge green";
  if (value.includes("Prohibited")) return "badge red";
  return "badge generic";
}

function stateBadge(value: string) {
  if (value === "approved") return "badge green";
  if (value === "ready") return "badge nist";
  if (value === "blocked") return "badge red";
  return "badge amber";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}
