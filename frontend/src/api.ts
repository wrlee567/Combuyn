// Thin typed client for the Combuyn API.
// In dev, Vite proxies these paths to the FastAPI backend (see vite.config.ts).
// In production (Vercel), set VITE_API_BASE_URL to the Render backend URL.

import {
  demoAIGovernanceSummary,
  demoAISystems,
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

export interface AIGovernanceSummary {
  ai_systems: number;
  iso42001_controls: number;
  high_risk_systems: number;
  gpai_systems: number;
  open_tasks: number;
  passing_guardrails: number;
  trust_center_frameworks: number;
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

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
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
  aiGovernanceSummary: () =>
    getOrDemo<AIGovernanceSummary>(
      "/api/ai-governance/summary",
      demoAIGovernanceSummary,
    ),
  aiSystems: () =>
    getOrDemo<AISystem[]>("/api/ai-governance/systems", demoAISystems),
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
  medicalAIRisks: () =>
    getOrDemo<MedicalAIRisk[]>(
      "/api/ai-governance/medical-risk",
      demoMedicalRisks,
    ),
  aiVendors: () =>
    getOrDemo<AIVendor[]>("/api/ai-governance/vendors", demoVendors),
  trustCenter: () =>
    getOrDemo<TrustCenter>("/api/trust-center", demoTrustCenter),
};
