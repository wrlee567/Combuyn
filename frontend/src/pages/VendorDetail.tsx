import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  api,
  type QuestionnaireTemplate,
  type VendorDetail as Vendor,
} from "../api";
import { humanize, riskClass } from "../badge";

const LIFECYCLE = [
  "sourcing",
  "onboarding",
  "assessment",
  "management",
  "monitoring",
  "offboarding",
];

export default function VendorDetail() {
  const { id = "" } = useParams();
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [template, setTemplate] = useState<QuestionnaireTemplate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.vendor(id), api.questionnaireTemplate()])
      .then(([v, t]) => {
        setVendor(v);
        setTemplate(t);
      })
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Loading vendor…</div>;
  if (error || !vendor)
    return (
      <>
        <a className="back-link" href="/vendors">
          ← Vendors
        </a>
        <div className="notice error">
          Couldn't load this vendor ({error}). Vendor detail needs the live
          backend — connect the API to view it.
        </div>
      </>
    );

  async function setLifecycle(status: string) {
    try {
      setVendor(await api.updateLifecycle(id, status));
      setNotice("Lifecycle updated.");
    } catch (e) {
      setError(String((e as Error).message));
    }
  }

  async function answer(qid: string, value: unknown) {
    try {
      const updated = await api.updateQuestionnaire(id, { [qid]: value });
      setVendor(updated);
      setNotice("Saved.");
    } catch (e) {
      setError(String((e as Error).message));
    }
  }

  const responses = vendor.questionnaire_responses ?? {};

  return (
    <>
      <a className="back-link" href="/vendors">
        ← Vendors
      </a>
      <div className="row">
        <h1 style={{ margin: 0 }}>{vendor.name}</h1>
        <span className={riskClass(vendor.inherent_risk_tier)}>
          {vendor.inherent_risk_tier} · {vendor.inherent_risk_score}
        </span>
      </div>

      {notice && <div className="notice success">{notice}</div>}

      <div className="panel">
        <h2>Profile</h2>
        <div className="kv">
          <div className="k">Contact</div>
          <div>
            {vendor.contact_name || "—"}{" "}
            {vendor.contact_email && (
              <span className="muted">&lt;{vendor.contact_email}&gt;</span>
            )}
          </div>
          <div className="k">Industry</div>
          <div>{humanize(vendor.industry)}</div>
          <div className="k">Data classification</div>
          <div>{humanize(vendor.data_classification)}</div>
          <div className="k">Network connectivity</div>
          <div>{humanize(vendor.network_connectivity)}</div>
          <div className="k">Geography</div>
          <div>{humanize(vendor.geography)}</div>
          <div className="k">Lifecycle phase</div>
          <div>
            <select
              aria-label="Lifecycle phase"
              value={vendor.lifecycle_status}
              onChange={(e) => setLifecycle(e.target.value)}
            >
              {LIFECYCLE.map((p) => (
                <option key={p} value={p}>
                  {humanize(p)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>Inherent Risk Breakdown</h2>
        <div className="kv">
          {Object.entries(vendor.risk_breakdown ?? {}).map(([factor, b]) => (
            <FactorRow key={factor} factor={factor} b={b} />
          ))}
        </div>
      </div>

      {template && (
        <div className="panel">
          <h2>Security Questionnaire</h2>
          {template.sections.map((section) => (
            <div className="q-section" key={section.section}>
              <h3>{section.section}</h3>
              {section.questions.map((q) => (
                <div className="q-row" key={q.id}>
                  <span className="q-text">{q.text}</span>
                  <QuestionInput
                    q={q}
                    value={responses[q.id]}
                    onChange={(v) => answer(q.id, v)}
                  />
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function FactorRow({
  factor,
  b,
}: {
  factor: string;
  b: { value: string; severity: number; weight: number; contribution: number };
}) {
  return (
    <>
      <div className="k">{humanize(factor)}</div>
      <div>
        {humanize(b.value)}{" "}
        <span className="muted">
          (severity {b.severity}/4, weight {Math.round(b.weight * 100)}%)
        </span>
      </div>
    </>
  );
}

function QuestionInput({
  q,
  value,
  onChange,
}: {
  q: QuestionnaireTemplate["sections"][number]["questions"][number];
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  if (q.type === "boolean") {
    return (
      <select
        aria-label={q.text}
        value={value === true ? "yes" : value === false ? "no" : ""}
        onChange={(e) =>
          onChange(e.target.value === "" ? null : e.target.value === "yes")
        }
      >
        <option value="">—</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    );
  }
  if (q.type === "single_select") {
    return (
      <select
        aria-label={q.text}
        value={(value as string) ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">—</option>
        {(q.options ?? []).map((o) => (
          <option key={o} value={o}>
            {humanize(o)}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      aria-label={q.text}
      value={(value as string) ?? ""}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
