// Thin typed client for the Combuyn API.
// In dev, Vite proxies these paths to the FastAPI backend (see vite.config.ts).
// In production (Vercel), set VITE_API_BASE_URL to the Render backend URL.

import {
  demoAIGovernanceSummary,
  demoAIVendors,
  demoAIReviews,
  demoAISystems,
  demoLaunchGate,
  demoCoverage,
  demoFrameworks,
  demoGuardrails,
  demoImpactAssessments,
  demoISO42001Controls,
  demoMedicalRisks,
  demoSummary,
  demoTasks,
  demoTrustCenter,
  demoVendors,
  demoWorkflowDefinitions,
  demoWorkflowInstances,
} from "./demoData";

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "combuyn.demoAccessToken";

// Demo fallback (bundled sample data) is opt-in via VITE_DEMO_MODE=true — useful
// for backendless previews. When off (the default, incl. production) API errors
// surface to the caller instead of being masked by demo data.
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

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

// ---- Workflow Orchestration (Iteration 3) ----

export interface BlueprintState {
  id: string;
  label?: string;
  type?: "start" | "end";
}

export interface BlueprintTransition {
  action: string;
  from: string;
  to: string;
  compensation?: string;
}

export interface Blueprint {
  initial: string;
  states: BlueprintState[];
  transitions: BlueprintTransition[];
}

export interface WorkflowDefinitionSummary {
  id: string;
  key: string;
  name: string;
  description: string;
}

export interface WorkflowDefinitionDetail extends WorkflowDefinitionSummary {
  blueprint: Blueprint;
}

export interface WorkflowEvent {
  sequence: number;
  kind: string;
  action: string;
  from_state: string;
  to_state: string;
  note: string;
}

export interface TransitionOption {
  action: string;
  target: string;
  compensation: string;
}

export interface WorkflowInstanceSummary {
  id: string;
  definition_id: string;
  subject: string;
  current_state: string;
  status: string;
}

export interface WorkflowInstanceDetail extends WorkflowInstanceSummary {
  definition_key: string;
  definition_name: string;
  context: Record<string, unknown>;
  blueprint: Blueprint;
  events: WorkflowEvent[];
  available_actions: TransitionOption[];
}

export interface InstanceCreate {
  definition_key: string;
  subject: string;
  context?: Record<string, unknown>;
}

export interface AIGovernanceSummary {
  ai_systems: number;
  iso42001_controls: number;
  high_risk_systems: number;
  gpai_systems: number;
  open_tasks: number;
  passing_guardrails: number;
  trust_center_frameworks: number;
  evidence_items: number;
  missing_evidence: number;
  overdue_reviews: number;
}

export interface AIClassification {
  id: string;
  actor_role: string;
  risk_tier: string;
  regulatory_scope: string;
  questionnaire_version: string;
  questionnaire_answers: Record<string, unknown>;
  rationale: string;
}

export interface AISystem {
  id: string;
  name: string;
  owner: string;
  business_purpose: string;
  source_type: string;
  provider_name: string;
  model_type: string;
  foundation_model_used: string;
  deployment_environment: string;
  lifecycle_stage: string;
  regulatory_role: string;
  eu_market: boolean;
  medical_device_related: boolean;
  customer_data_training_policy: string;
  prompt_completion_training_policy: string;
  data_classes: Record<string, unknown>;
  latest_classification: AIClassification | null;
}

export interface ISO42001Control {
  id: string;
  objective_code: string;
  objective_title: string;
  control_id: string;
  title: string;
  description: string;
  implementation_guidance: string;
  audit_evidence: string;
}

export interface AIComplianceTask {
  id: string;
  ai_system_id: string;
  system_name: string;
  framework: string;
  obligation: string;
  owner_role: string;
  status: string;
  due_offset_days: number;
  evidence_required: string[];
}

export interface AIGuardrail {
  ai_system_id: string;
  system_name: string;
  privacy_status: string;
  customer_data_training_blocked: boolean;
  prompt_completion_training_blocked: boolean;
  retention_policy: string;
  infrastructure_status: string;
  model_isolation_confirmed: boolean;
  encryption_at_rest: boolean;
  encryption_in_transit: boolean;
  private_network_path: boolean;
  network_path_type: string;
}

export interface AIImpactAssessment {
  id: string;
  ai_system_id: string;
  system_name: string;
  lifecycle_stage: string;
  mandatory_review_status: string;
  nist_govern: Record<string, unknown>;
  nist_map: Record<string, unknown>;
  nist_measure: Record<string, unknown>;
  nist_manage: Record<string, unknown>;
  data_provenance: string;
  data_quality: string;
  training_data_protections: string;
  residual_risk: string;
  approval_status: string;
}

export interface AIEvidenceItem {
  id: string;
  requirement: string;
  evidence_type: string;
  title: string;
  evidence_uri: string;
  owner: string;
  status: string;
  notes: string;
}

export interface AIGovernanceReview {
  id: string;
  ai_system_id: string;
  system_name: string;
  review_name: string;
  review_type: string;
  status: string;
  risk_level: string;
  reviewer: string;
  decision_summary: string;
  next_review_date: string | null;
  evidence_ready: number;
  evidence_missing: number;
  evidence_items: AIEvidenceItem[];
}

export interface MedicalAIRisk {
  id: string;
  ai_system_id: string;
  system_name: string;
  soup_component: string;
  training_validation_test_split_risk: string;
  explainable_ai_evaluation: string;
  performative_prediction_risk: string;
  clinical_validation_status: string;
  risk_controls: string;
  review_status: string;
}

export interface AIVendor {
  id: string;
  name: string;
  service: string;
  onboarding_status: string;
  sbom_received: boolean;
  sbom_format: string;
  supply_chain_risk: string;
  data_processing_role: string;
  evidence_uri: string;
}

export interface TrustFramework {
  id: string;
  framework: string;
  status: string;
  coverage_percent: number;
  monitored_controls: number;
  public_summary: string;
}

export interface TrustTransparency {
  id: string;
  ai_system_id: string | null;
  system_name: string;
  direct_user_interaction: boolean;
  biometric_data: boolean;
  synthetic_content: boolean;
  deepfake_generation: boolean;
  eu_transparency_notice: string;
  public_summary: string;
}

export interface TrustDocument {
  id: string;
  document_name: string;
  sensitivity: string;
  nda_required: boolean;
  nda_status: string;
  request_workflow: string;
  fulfillment_status: string;
}

export interface TrustCenter {
  frameworks: TrustFramework[];
  ai_transparency: TrustTransparency[];
  documents: TrustDocument[];
}

export interface LaunchGateReadiness {
  score: number;
  state: string;
  evidence_ready: number;
  evidence_total: number;
  evidence_missing: number;
  evidence_rejected: number;
  guardrails_passing: number;
  guardrails_total: number;
  tasks_complete: number;
  tasks_total: number;
  approval_blockers: string[];
}

export interface AILaunchGate {
  system: AISystem;
  latest_classification: AIClassification | null;
  tasks: AIComplianceTask[];
  guardrails: AIGuardrail | null;
  impact_assessment: AIImpactAssessment | null;
  governance_review: AIGovernanceReview | null;
  evidence_items: AIEvidenceItem[];
  trust_center_transparency: TrustTransparency | null;
  readiness: LaunchGateReadiness;
}

export interface EvidencePatch {
  status?: "missing" | "provided" | "accepted" | "rejected";
  evidence_uri?: string;
  notes?: string;
}

export interface ReviewDecisionPatch {
  status: string;
  decision_summary: string;
  next_review_date: string | null;
}

type ResponseBody =
  | { kind: "json"; value: unknown }
  | { kind: "text"; value: string; contentType: string };

interface DemoTokenResponse {
  access_token: string;
  token_type: "bearer";
}

function apiUrl(path: string): string {
  if (!BASE && import.meta.env.PROD && !DEMO_MODE) {
    throw new Error(
      "VITE_API_BASE_URL is not configured. Set it to the deployed backend URL or enable VITE_DEMO_MODE=true for a backendless preview.",
    );
  }
  return `${BASE}${path}`;
}

function storedToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

function saveToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function clearToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function fetchDemoToken(): Promise<string> {
  const res = await fetch(apiUrl("/auth/demo-token"), { method: "POST" });
  const body = await readBody(res, "/auth/demo-token");

  if (!res.ok) {
    const detail = body.kind === "json" ? detailFromJson(body.value) : null;
    throw new Error(detail ?? nonJsonMessage("/auth/demo-token", res.status, body));
  }

  if (body.kind !== "json") {
    throw new Error(nonJsonMessage("/auth/demo-token", res.status, body));
  }

  const token = (body.value as DemoTokenResponse).access_token;
  if (!token) {
    throw new Error("/auth/demo-token did not return an access token.");
  }
  saveToken(token);
  return token;
}

async function tokenForRequest(): Promise<string> {
  return storedToken() ?? fetchDemoToken();
}

function withAuth(init: RequestInit | undefined, token: string): RequestInit {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return { ...init, headers };
}

function looksLikeJson(text: string): boolean {
  const trimmed = text.trim();
  return trimmed.startsWith("{") || trimmed.startsWith("[");
}

async function readBody(res: Response, path: string): Promise<ResponseBody> {
  const contentType = res.headers.get("content-type") ?? "";
  const text = await res.text();

  if (!text) {
    return { kind: "json", value: null };
  }

  if (contentType.includes("application/json") || looksLikeJson(text)) {
    try {
      return { kind: "json", value: JSON.parse(text) };
    } catch {
      throw new Error(`${path} returned invalid JSON from the API.`);
    }
  }

  return { kind: "text", value: text, contentType };
}

function detailFromJson(value: unknown): string | null {
  if (value && typeof value === "object" && "detail" in value) {
    return formatApiDetail((value as { detail: unknown }).detail);
  }
  return null;
}

function formatApiDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc =
            "loc" in item && Array.isArray((item as { loc: unknown }).loc)
              ? ` (${(item as { loc: unknown[] }).loc.join(".")})`
              : "";
          return `${String((item as { msg: unknown }).msg)}${loc}`;
        }
        return formatApiDetail(item);
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }

  return String(detail);
}

function nonJsonMessage(path: string, status: number, body: ResponseBody): string {
  if (body.kind === "json") {
    return `${path} -> ${status}`;
  }

  if (body.contentType.includes("text/html")) {
    return `${path} returned HTML instead of JSON. Check VITE_API_BASE_URL or the /api rewrite.`;
  }

  const preview = body.value.trim().replace(/\s+/g, " ").slice(0, 120);
  return `${path} returned ${body.contentType || "a non-JSON response"} (${status})${
    preview ? `: ${preview}` : ""
  }`;
}

async function request<T>(
  path: string,
  init?: RequestInit,
  retryOnUnauthorized = true,
): Promise<T> {
  const requestInit = DEMO_MODE
    ? init
    : withAuth(init, await tokenForRequest());
  const res = await fetch(apiUrl(path), requestInit);
  const body = await readBody(res, path);

  if (!DEMO_MODE && res.status === 401 && retryOnUnauthorized) {
    clearToken();
    await fetchDemoToken();
    return request<T>(path, init, false);
  }

  if (!res.ok) {
    const detail = body.kind === "json" ? detailFromJson(body.value) : null;
    throw new Error(detail ?? nonJsonMessage(path, res.status, body));
  }

  if (body.kind !== "json") {
    throw new Error(nonJsonMessage(path, res.status, body));
  }

  return body.value as T;
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

async function send<T>(path: string, method: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function updateDemoEvidence(id: string, body: EvidencePatch): AIEvidenceItem {
  for (const review of demoAIReviews) {
    const item = review.evidence_items.find((evidence) => evidence.id === id);
    if (!item) continue;
    Object.assign(item, body);
    review.evidence_ready = review.evidence_items.filter((evidence) =>
      ["accepted", "provided"].includes(evidence.status),
    ).length;
    review.evidence_missing = review.evidence_items.filter(
      (evidence) => evidence.status === "missing",
    ).length;
    return item;
  }
  throw new Error("Evidence item not found");
}

function updateDemoReviewDecision(
  id: string,
  body: ReviewDecisionPatch,
): AIGovernanceReview {
  const review = demoAIReviews.find((candidate) => candidate.id === id);
  if (!review) throw new Error("Governance review not found");
  if (
    ["approved", "approved with conditions"].includes(body.status) &&
    review.evidence_items.some((item) => ["missing", "rejected"].includes(item.status))
  ) {
    throw new Error("Missing or rejected evidence blocks approval.");
  }
  review.status = body.status;
  review.decision_summary = body.decision_summary;
  review.next_review_date = body.next_review_date;
  return review;
}
// In demo mode, fall back to bundled demo data when the API is unreachable
// (e.g. a Vercel preview with no backend wired up). Otherwise, errors propagate
// so the UI can show a real error/empty state instead of fake-healthy data.
async function getOrDemo<T>(path: string, demo: T): Promise<T> {
  if (!DEMO_MODE) {
    return get<T>(path);
  }
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
  workflowDefinitions: () =>
    getOrDemo<WorkflowDefinitionSummary[]>(
      "/api/workflows/definitions",
      demoWorkflowDefinitions
    ),
  workflowInstances: () =>
    getOrDemo<WorkflowInstanceSummary[]>(
      "/api/workflows",
      demoWorkflowInstances
    ),
  workflowInstance: (id: string) =>
    get<WorkflowInstanceDetail>(`/api/workflows/${id}`),
  createWorkflowInstance: (body: InstanceCreate) =>
    send<WorkflowInstanceDetail>("/api/workflows", "POST", body),
  advanceWorkflow: (id: string, action: string) =>
    send<WorkflowInstanceDetail>(`/api/workflows/${id}/advance`, "POST", {
      action,
    }),
  compensateWorkflow: (id: string) =>
    send<WorkflowInstanceDetail>(`/api/workflows/${id}/compensate`, "POST", {}),

  aiGovernanceSummary: () =>
    getOrDemo<AIGovernanceSummary>(
      "/api/ai-governance/summary",
      demoAIGovernanceSummary,
    ),
  aiSystems: () =>
    getOrDemo<AISystem[]>("/api/ai-governance/systems", demoAISystems),
  aiLaunchGate: (id: string) =>
    getOrDemo<AILaunchGate>(
      `/api/ai-governance/systems/${id}/launch-gate`,
      demoLaunchGate(id),
    ),
  iso42001Controls: () =>
    getOrDemo<ISO42001Control[]>(
      "/api/ai-governance/iso42001/controls",
      demoISO42001Controls,
    ),
  aiTasks: () =>
    getOrDemo<AIComplianceTask[]>("/api/ai-governance/tasks", demoTasks),
  aiGuardrails: () =>
    getOrDemo<AIGuardrail[]>("/api/ai-governance/guardrails", demoGuardrails),
  aiImpactAssessments: () =>
    getOrDemo<AIImpactAssessment[]>(
      "/api/ai-governance/impact-assessments",
      demoImpactAssessments,
    ),
  aiReviews: () =>
    getOrDemo<AIGovernanceReview[]>(
      "/api/ai-governance/reviews",
      demoAIReviews,
    ),
  updateAIEvidence: (id: string, body: EvidencePatch) =>
    DEMO_MODE
      ? Promise.resolve(updateDemoEvidence(id, body))
      : send<AIEvidenceItem>(`/api/ai-governance/evidence/${id}`, "PATCH", body),
  updateAIReviewDecision: (id: string, body: ReviewDecisionPatch) =>
    DEMO_MODE
      ? Promise.resolve(updateDemoReviewDecision(id, body))
      : send<AIGovernanceReview>(
          `/api/ai-governance/reviews/${id}/decision`,
          "PATCH",
          body,
        ),
  medicalAIRisks: () =>
    getOrDemo<MedicalAIRisk[]>(
      "/api/ai-governance/medical-risk",
      demoMedicalRisks,
    ),
  aiVendors: () =>
    getOrDemo<AIVendor[]>("/api/ai-governance/vendors", demoAIVendors),
  trustCenter: () =>
    getOrDemo<TrustCenter>("/api/trust-center", demoTrustCenter),
};
