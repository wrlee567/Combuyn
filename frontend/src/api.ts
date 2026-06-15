// Thin typed client for the Combuyn API.
// In dev, Vite proxies these paths to the FastAPI backend (see vite.config.ts).
// In production (Vercel), set VITE_API_BASE_URL to the Render backend URL.

import {
  demoCoverage,
  demoFrameworks,
  demoSummary,
  demoVendors,
} from "./demoData";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface Summary {
  frameworks: number;
  requirements: number;
  common_controls: number;
  mappings: number;
}

export interface Framework {
  id: string;
  key: string;
  name: string;
  version: string;
  authority: string;
  description: string;
  category: string;
  requirement_count: number;
}

export interface RequirementRef {
  framework_key: string;
  framework_name: string;
  citation: string;
  title: string;
  relationship_type: string;
}

export interface ControlCoverage {
  id: string;
  key: string;
  name: string;
  domain: string;
  description: string;
  frameworks_covered: string[];
  requirements: RequirementRef[];
}

export interface VendorSummary {
  id: string;
  name: string;
  industry: string;
  lifecycle_status: string;
  inherent_risk_score: number;
  inherent_risk_tier: string;
}

export interface VendorDetail extends VendorSummary {
  contact_name: string;
  contact_email: string;
  description: string;
  data_classification: string;
  network_connectivity: string;
  geography: string;
  risk_breakdown: Record<
    string,
    { value: string; severity: number; weight: number; contribution: number }
  >;
  questionnaire_responses: Record<string, unknown>;
}

export interface VendorCreate {
  name: string;
  contact_name?: string;
  contact_email?: string;
  description?: string;
  industry: string;
  data_classification: string;
  network_connectivity: string;
  geography: string;
  lifecycle_status?: string;
}

export interface VendorOptions {
  factors: Record<string, string[]>;
  lifecycle_phases: string[];
}

export interface QuestionnaireTemplate {
  version: string;
  sections: {
    section: string;
    ccf_domain: string;
    questions: {
      id: string;
      text: string;
      type: "boolean" | "single_select" | "text";
      options?: string[];
    }[];
  }[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function send<T>(path: string, method: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(String(detail));
  }
  return res.json() as Promise<T>;
}

// Try the live API; if it's unreachable (e.g. a Vercel preview with no backend
// wired up yet), fall back to bundled demo data so the UI stays populated.
async function getOrDemo<T>(path: string, demo: T): Promise<T> {
  try {
    return await get<T>(path);
  } catch {
    return demo;
  }
}

export const api = {
  summary: () => getOrDemo<Summary>("/api/summary", demoSummary),
  frameworks: () => getOrDemo<Framework[]>("/api/frameworks", demoFrameworks),
  coverage: () => getOrDemo<ControlCoverage[]>("/api/coverage", demoCoverage),

  vendors: () => getOrDemo<VendorSummary[]>("/api/vendors", demoVendors),
  vendor: (id: string) => get<VendorDetail>(`/api/vendors/${id}`),
  vendorOptions: () => get<VendorOptions>("/api/vendors/options"),
  questionnaireTemplate: () =>
    get<QuestionnaireTemplate>("/api/vendors/questionnaire-template"),
  createVendor: (body: VendorCreate) =>
    send<VendorDetail>("/api/vendors", "POST", body),
  updateQuestionnaire: (id: string, responses: Record<string, unknown>) =>
    send<VendorDetail>(`/api/vendors/${id}/questionnaire`, "PATCH", { responses }),
  updateLifecycle: (id: string, lifecycle_status: string) =>
    send<VendorDetail>(`/api/vendors/${id}/lifecycle`, "PATCH", {
      lifecycle_status,
    }),
};
