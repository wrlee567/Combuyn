"""Pydantic schemas for the AI Governance API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AIInventorySummary(BaseModel):
    ai_systems: int
    iso42001_controls: int
    high_risk_systems: int
    gpai_systems: int
    open_tasks: int
    passing_guardrails: int
    trust_center_frameworks: int


class ISO42001ControlOut(ORMModel):
    id: uuid.UUID
    objective_code: str
    objective_title: str
    control_id: str
    title: str
    description: str
    implementation_guidance: str
    audit_evidence: str


class AIClassificationOut(ORMModel):
    id: uuid.UUID
    actor_role: str
    risk_tier: str
    regulatory_scope: str
    questionnaire_version: str
    questionnaire_answers: dict[str, object]
    rationale: str


class AISystemOut(ORMModel):
    id: uuid.UUID
    name: str
    owner: str
    business_purpose: str
    source_type: str
    provider_name: str
    model_type: str
    foundation_model_used: str
    deployment_environment: str
    lifecycle_stage: str
    regulatory_role: str
    eu_market: bool
    medical_device_related: bool
    customer_data_training_policy: str
    prompt_completion_training_policy: str
    data_classes: dict[str, object]
    latest_classification: AIClassificationOut | None = None


class AIComplianceTaskOut(ORMModel):
    id: uuid.UUID
    ai_system_id: uuid.UUID
    framework: str
    obligation: str
    owner_role: str
    status: str
    due_offset_days: int
    evidence_required: list[str]
    system_name: str = ""


class GuardrailOut(BaseModel):
    ai_system_id: uuid.UUID
    system_name: str
    privacy_status: str
    customer_data_training_blocked: bool
    prompt_completion_training_blocked: bool
    retention_policy: str
    infrastructure_status: str
    model_isolation_confirmed: bool
    encryption_at_rest: bool
    encryption_in_transit: bool
    private_network_path: bool
    network_path_type: str


class AIImpactAssessmentOut(ORMModel):
    id: uuid.UUID
    ai_system_id: uuid.UUID
    lifecycle_stage: str
    mandatory_review_status: str
    nist_govern: dict[str, object]
    nist_map: dict[str, object]
    nist_measure: dict[str, object]
    nist_manage: dict[str, object]
    data_provenance: str
    data_quality: str
    training_data_protections: str
    residual_risk: str
    approval_status: str
    system_name: str = ""


class MedicalAIRiskOut(ORMModel):
    id: uuid.UUID
    ai_system_id: uuid.UUID
    training_validation_test_split_risk: str
    explainable_ai_evaluation: str
    performative_prediction_risk: str
    clinical_validation_status: str
    risk_controls: str
    review_status: str
    system_name: str = ""
    soup_component: str = ""


class VendorProviderOut(ORMModel):
    id: uuid.UUID
    name: str
    service: str
    onboarding_status: str
    sbom_received: bool
    sbom_format: str
    supply_chain_risk: str
    data_processing_role: str
    evidence_uri: str


class ClassificationQuestionOut(BaseModel):
    key: str
    text: str
    category: str


class AIClassificationRequest(BaseModel):
    ai_system_id: uuid.UUID
    actor_role: str
    questionnaire_answers: dict[str, object]


class TrustFrameworkOut(ORMModel):
    id: uuid.UUID
    framework: str
    status: str
    coverage_percent: int
    monitored_controls: int
    public_summary: str


class TrustTransparencyOut(ORMModel):
    id: uuid.UUID
    system_name: str
    direct_user_interaction: bool
    biometric_data: bool
    synthetic_content: bool
    deepfake_generation: bool
    eu_transparency_notice: str
    public_summary: str


class TrustDocumentOut(ORMModel):
    id: uuid.UUID
    document_name: str
    sensitivity: str
    nda_required: bool
    nda_status: str
    request_workflow: str
    fulfillment_status: str


class TrustCenterOut(BaseModel):
    frameworks: list[TrustFrameworkOut]
    ai_transparency: list[TrustTransparencyOut]
    documents: list[TrustDocumentOut]
