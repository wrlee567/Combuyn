import { useNavigate } from "react-router-dom";
import { api, type AIGovernanceReview, type ISO42001Control } from "../api";
import { badgeClass } from "../badge";
import { useApi } from "../useApi";

export default function AIGovernance() {
  const navigate = useNavigate();
  const summary = useApi(api.aiGovernanceSummary);
  const systems = useApi(api.aiSystems);
  const controls = useApi(api.iso42001Controls);
  const tasks = useApi(api.aiTasks);
  const guardrails = useApi(api.aiGuardrails);
  const impacts = useApi(api.aiImpactAssessments);
  const reviews = useApi(api.aiReviews);
  const medical = useApi(api.medicalAIRisks);
  const vendors = useApi(api.aiVendors);

  if (
    summary.loading ||
    systems.loading ||
    controls.loading ||
    tasks.loading ||
    guardrails.loading ||
    impacts.loading ||
    reviews.loading ||
    medical.loading ||
    vendors.loading
  ) {
    return <div className="loading">Loading AI governance workspace...</div>;
  }

  if (summary.error) return <div className="error">API error: {summary.error}</div>;

  const s = summary.data!;
  const groupedControls = groupControlsByObjective(controls.data ?? []);

  return (
    <>
      <h1>AI Governance</h1>
      <p className="subtitle">
        AI inventory, risk classification, impact assessment, privacy guardrails,
        vendor evidence, and Trust Center readiness.
      </p>

      <div className="cards ai-cards">
        <Stat value={s.ai_systems} label="AI Systems" />
        <Stat value={s.iso42001_controls} label="ISO 42001 Controls" />
        <Stat value={s.high_risk_systems} label="High-Risk Systems" />
        <Stat value={s.gpai_systems} label="GPAI Models" />
        <Stat value={s.open_tasks} label="Open AI Tasks" />
        <Stat value={s.passing_guardrails} label="Passing Guardrails" />
        <Stat value={s.missing_evidence} label="Missing Evidence" />
        <Stat value={s.overdue_reviews} label="Overdue Reviews" />
      </div>

      <div className="panel">
        <h2>AI System Inventory</h2>
        <table>
          <thead>
            <tr>
              <th>System</th>
              <th>EU AI Act Tier</th>
              <th>Role</th>
              <th>Lifecycle</th>
              <th>Privacy Boundary</th>
            </tr>
          </thead>
          <tbody>
            {(systems.data ?? []).map((system) => (
              <tr
                className="clickable"
                key={system.id}
                tabIndex={0}
                onClick={() => navigate(`/ai-governance/systems/${system.id}`)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    navigate(`/ai-governance/systems/${system.id}`);
                  }
                }}
              >
                <td>
                  <div className="control-key">{system.name}</div>
                  <div>{system.business_purpose}</div>
                  <div className="domain">
                    {system.source_type} - {system.provider_name}
                  </div>
                </td>
                <td>
                  <span className={riskBadge(system.latest_classification?.risk_tier)}>
                    {system.latest_classification?.risk_tier ?? "Unclassified"}
                  </span>
                  <div className="domain">
                    {system.latest_classification?.regulatory_scope ?? "review required"}
                  </div>
                </td>
                <td>{system.regulatory_role}</td>
                <td>{system.lifecycle_stage}</td>
                <td>
                  <div>{system.customer_data_training_policy}</div>
                  <div className="domain">{system.prompt_completion_training_policy}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <div className="panel-heading">
          <div>
            <h2>AI Risk and Evidence Register</h2>
            <p className="panel-subtitle">
              Approval status, review cadence, and evidence readiness for governed AI systems.
            </p>
          </div>
          <span className="badge generic">{s.evidence_items} evidence items</span>
        </div>
        <div className="review-grid">
          {(reviews.data ?? []).map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <h2>ISO/IEC 42001 Annex A</h2>
          <div className="objective-list">
            {Object.entries(groupedControls).map(([objective, group]) => (
              <div className="objective-row" key={objective}>
                <div>
                  <div className="control-key">{objective}</div>
                  <div>{group.title}</div>
                </div>
                <span className="badge generic">{group.controls.length} controls</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Generated Compliance Tasks</h2>
          <div className="task-list">
            {(tasks.data ?? []).slice(0, 6).map((task) => (
              <div className="task-row" key={task.id}>
                <div>
                  <div className="control-key">{task.system_name}</div>
                  <div>{task.obligation}</div>
                  <div className="domain">
                    {task.framework} - {task.owner_role} - due +{task.due_offset_days}d
                  </div>
                </div>
                <span className={badgeClass(task.status)}>{task.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>Privacy and Deployment Guardrails</h2>
        <table>
          <thead>
            <tr>
              <th>System</th>
              <th>Training Exclusion</th>
              <th>Deployment</th>
              <th>Network</th>
            </tr>
          </thead>
          <tbody>
            {(guardrails.data ?? []).map((guardrail) => (
              <tr key={guardrail.ai_system_id}>
                <td>{guardrail.system_name}</td>
                <td>
                  <span className={guardrail.customer_data_training_blocked ? "badge green" : "badge amber"}>
                    customer data blocked
                  </span>
                  <span className={guardrail.prompt_completion_training_blocked ? "badge green" : "badge amber"}>
                    prompts blocked
                  </span>
                </td>
                <td>
                  <span className={guardrail.model_isolation_confirmed ? "badge green" : "badge amber"}>
                    isolated
                  </span>
                  <span className={guardrail.encryption_at_rest ? "badge green" : "badge amber"}>
                    encrypted at rest
                  </span>
                  <span className={guardrail.encryption_in_transit ? "badge green" : "badge amber"}>
                    encrypted in transit
                  </span>
                </td>
                <td>
                  <span className={guardrail.private_network_path ? "badge green" : "badge amber"}>
                    {guardrail.network_path_type}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="split">
        <div className="panel">
          <h2>NIST AI RMF Impact Assessments</h2>
          <div className="task-list">
            {(impacts.data ?? []).map((impact) => (
              <div className="task-row" key={impact.id}>
                <div>
                  <div className="control-key">{impact.system_name}</div>
                  <div className="four-function-grid">
                    <MiniMetric label="Govern" value={compactValue(impact.nist_govern)} />
                    <MiniMetric label="Map" value={compactValue(impact.nist_map)} />
                    <MiniMetric label="Measure" value={compactValue(impact.nist_measure)} />
                    <MiniMetric label="Manage" value={compactValue(impact.nist_manage)} />
                  </div>
                  <div className="domain">
                    {impact.lifecycle_stage} - {impact.mandatory_review_status}
                  </div>
                </div>
                <span className={riskBadge(impact.residual_risk)}>{impact.residual_risk}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Vendor SBOM and Medical AI Risk</h2>
          <div className="task-list">
            {(vendors.data ?? []).map((vendor) => (
              <div className="task-row" key={vendor.id}>
                <div>
                  <div className="control-key">{vendor.name}</div>
                  <div>{vendor.service}</div>
                  <div className="domain">
                    {vendor.onboarding_status} - {vendor.data_processing_role}
                  </div>
                </div>
                <span className={vendor.sbom_received ? "badge green" : "badge amber"}>
                  {vendor.sbom_received ? vendor.sbom_format : "SBOM required"}
                </span>
              </div>
            ))}
            {(medical.data ?? []).map((risk) => (
              <div className="medical-risk" key={risk.id}>
                <div className="control-key">{risk.system_name}</div>
                <div>{risk.training_validation_test_split_risk}</div>
                <div className="domain">{risk.soup_component}</div>
                <div className="domain">{risk.explainable_ai_evaluation}</div>
                <div className="domain">{risk.performative_prediction_risk}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function groupControlsByObjective(controls: ISO42001Control[]) {
  return controls.reduce<Record<string, { title: string; controls: ISO42001Control[] }>>(
    (acc, control) => {
      acc[control.objective_code] ??= {
        title: control.objective_title,
        controls: [],
      };
      acc[control.objective_code].controls.push(control);
      return acc;
    },
    {},
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

function compactValue(value: Record<string, unknown>) {
  return Object.values(value)
    .flatMap((item) => (Array.isArray(item) ? item : [item]))
    .slice(0, 2)
    .map(String)
    .join(", ");
}

function ReviewCard({ review }: { review: AIGovernanceReview }) {
  const totalEvidence = review.evidence_items.length || 1;
  const readyPercent = Math.round((review.evidence_ready / totalEvidence) * 100);
  const overdue =
    review.next_review_date !== null &&
    new Date(`${review.next_review_date}T00:00:00`) < new Date();

  return (
    <div className="review-card">
      <div className="review-card-header">
        <div>
          <div className="control-key">{review.system_name}</div>
          <h3>{review.review_name}</h3>
        </div>
        <span className={riskBadge(review.risk_level)}>{review.risk_level}</span>
      </div>
      <div className="review-meta">
        <span className={badgeClass(review.status)}>{review.status}</span>
        <span className={overdue ? "badge amber" : "badge generic"}>
          {review.next_review_date ? formatDate(review.next_review_date) : "unscheduled"}
        </span>
        <span className="badge generic">{review.reviewer}</span>
      </div>
      <p>{review.decision_summary}</p>
      <div className="evidence-progress">
        <div>
          <strong>{review.evidence_ready}</strong> ready
        </div>
        <div>
          <strong>{review.evidence_missing}</strong> missing
        </div>
      </div>
      <div className="progress-bar evidence-bar">
        <div style={{ width: `${readyPercent}%` }} />
      </div>
      <div className="evidence-list">
        {review.evidence_items.map((item) => (
          <div className="evidence-row" key={item.id}>
            <div>
              <div>{item.requirement}</div>
              <div className="domain">{item.title}</div>
            </div>
            <span className={evidenceBadge(item.status)}>{item.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function evidenceBadge(status: string) {
  if (status === "accepted") return "badge green";
  if (status === "provided") return "badge nist";
  if (status === "missing") return "badge amber";
  return "badge generic";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="card">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="mini-metric">
      <div className="domain">{label}</div>
      <div>{value}</div>
    </div>
  );
}
