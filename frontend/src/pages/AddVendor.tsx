import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type VendorCreate, type VendorOptions } from "../api";
import { humanize } from "../badge";

// Fallback factor options so the form still renders on a backend-less preview.
const FALLBACK_OPTIONS: VendorOptions = {
  factors: {
    industry: [
      "technology",
      "manufacturing",
      "retail",
      "professional_services",
      "financial_services",
      "healthcare",
      "government",
      "medical_devices",
      "other",
    ],
    data_classification: ["public", "internal", "confidential", "restricted"],
    network_connectivity: ["none", "limited", "integrated", "privileged"],
    geography: ["domestic", "eu_eea", "international", "high_risk"],
  },
  lifecycle_phases: [
    "sourcing",
    "onboarding",
    "assessment",
    "management",
    "monitoring",
    "offboarding",
  ],
};

export default function AddVendor() {
  const navigate = useNavigate();
  const [options, setOptions] = useState<VendorOptions>(FALLBACK_OPTIONS);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState<VendorCreate>({
    name: "",
    contact_name: "",
    contact_email: "",
    description: "",
    industry: "technology",
    data_classification: "internal",
    network_connectivity: "limited",
    geography: "domestic",
    lifecycle_status: "sourcing",
  });

  useEffect(() => {
    api.vendorOptions().then(setOptions).catch(() => setOptions(FALLBACK_OPTIONS));
  }, []);

  function set<K extends keyof VendorCreate>(key: K, value: VendorCreate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const created = await api.createVendor(form);
      navigate(`/vendors/${created.id}`);
    } catch (err) {
      setError(String((err as Error).message ?? err));
      setSaving(false);
    }
  }

  const Select = (key: keyof VendorCreate, label: string, list: string[]) => (
    <div className="field">
      <label htmlFor={`vendor-${key}`}>{label}</label>
      <select
        id={`vendor-${key}`}
        value={form[key] as string}
        onChange={(e) => set(key, e.target.value)}
      >
        {list.map((o) => (
          <option key={o} value={o}>
            {humanize(o)}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <>
      <a className="back-link" href="/vendors">
        ← Vendors
      </a>
      <h1>Add Vendor</h1>
      <p className="subtitle">
        We'll compute the inherent risk score from these factors on save.
      </p>

      {error && <div className="notice error">{error}</div>}

      <form className="panel" onSubmit={submit}>
        <div className="form-grid">
          <div className="field full">
            <label htmlFor="vendor-name">Vendor name *</label>
            <input
              id="vendor-name"
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Acme Corp"
            />
          </div>
          <div className="field">
            <label htmlFor="vendor-contact-name">Contact name</label>
            <input
              id="vendor-contact-name"
              value={form.contact_name}
              onChange={(e) => set("contact_name", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="vendor-contact-email">Contact email</label>
            <input
              id="vendor-contact-email"
              type="email"
              value={form.contact_email}
              onChange={(e) => set("contact_email", e.target.value)}
            />
          </div>
          {Select("industry", "Industry", options.factors.industry)}
          {Select(
            "data_classification",
            "Data classification",
            options.factors.data_classification
          )}
          {Select(
            "network_connectivity",
            "Network connectivity",
            options.factors.network_connectivity
          )}
          {Select("geography", "Geography", options.factors.geography)}
          {Select(
            "lifecycle_status",
            "Lifecycle phase",
            options.lifecycle_phases
          )}
          <div className="field full">
            <label htmlFor="vendor-description">Description</label>
            <textarea
              id="vendor-description"
              rows={2}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </div>
        </div>
        <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
          <button className="btn" type="submit" disabled={saving || !form.name}>
            {saving ? "Saving…" : "Create vendor"}
          </button>
          <a className="btn secondary" href="/vendors">
            Cancel
          </a>
        </div>
      </form>
    </>
  );
}
