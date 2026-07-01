"""Pydantic schemas for the AI Governance API."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.ai_governance import EU_AI_ACT_QUESTIONNAIRE

_AI_ANSWER_KEYS = {q["key"] for q in EU_AI_ACT_QUESTIONNAIRE}


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
    evidence_items: int = 0
    missing_evidence: int = 0
    overdue_reviews: int = 0


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


class AIEvidenceItemOut(ORMModel):
    id: uuid.UUID
    requirement: str
    evidence_type: str
    title: str
    evidence_uri: str
    owner: str
    status: str
    reviewer_decision: str = ""
    reviewer_notes: str = ""
    notes: str


class AIImplementationPacketOut(BaseModel):
    id: str
    review_id: uuid.UUID
    evidence_id: uuid.UUID
    requirement_name: str
    source_framework: str
    regulatory_driver: str
    implementation_steps: list[str]
    evidence_requirements: list[str]
    owner: str
    due_date: date | None
    review_cadence: str
    status: str
    evidence_status: str
    evidence_uri: str
    acceptance_criteria: list[str]
    current_evidence_title: str
    reviewer_decision: str = ""
    reviewer_notes: str = ""


class AIGovernanceReviewOut(ORMModel):
    id: uuid.UUID
    ai_system_id: uuid.UUID
    system_name: str = ""
    review_name: str
    review_type: str
    status: str
    risk_level: str
    reviewer: str
    decision_summary: str
    next_review_date: date | None
    evidence_ready: int = 0
    evidence_missing: int = 0
    evidence_items: list[AIEvidenceItemOut] = Field(default_factory=list)


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

    @field_validator("questionnaire_answers")
    @classmethod
    def _validate_answers(cls, value: dict[str, object]) -> dict[str, object]:
        unknown = sorted(set(value) - _AI_ANSWER_KEYS)
        if unknown:
            raise ValueError(f"Unknown questionnaire keys: {', '.join(unknown)}")
        # Require real booleans so string truthiness (e.g. "false") can't flip
        # a classification.
        non_bool = sorted(k for k, v in value.items() if not isinstance(v, bool))
        if non_bool:
            raise ValueError(
                f"Answers must be booleans; non-boolean values for: {', '.join(non_bool)}"
            )
        return value


class TrustFrameworkOut(ORMModel):
    id: uuid.UUID
    framework: str
    status: str
    coverage_percent: int
    monitored_controls: int
    public_summary: str


class TrustTransparencyOut(ORMModel):
    id: uuid.UUID
    ai_system_id: uuid.UUID | None = None
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


class LaunchGateReadiness(BaseModel):
    score: int
    state: str
    evidence_ready: int
    evidence_total: int
    evidence_missing: int
    evidence_rejected: int
    guardrails_passing: int
    guardrails_total: int
    tasks_complete: int
    tasks_total: int
    approval_blockers: list[str] = Field(default_factory=list)


class AILaunchGateOut(BaseModel):
    system: AISystemOut
    latest_classification: AIClassificationOut | None
    tasks: list[AIComplianceTaskOut]
    guardrails: GuardrailOut | None
    impact_assessment: AIImpactAssessmentOut | None
    governance_review: AIGovernanceReviewOut | None
    evidence_items: list[AIEvidenceItemOut]
    trust_center_transparency: TrustTransparencyOut | None
    readiness: LaunchGateReadiness


class AIEvidencePatch(BaseModel):
    status: str | None = None
    evidence_uri: str | None = None
    reviewer_decision: str | None = None
    reviewer_notes: str | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"missing", "provided", "accepted", "rejected"}
        if value not in allowed:
            raise ValueError(
                f"Invalid evidence status. Allowed statuses: {', '.join(sorted(allowed))}"
            )
        return value

    @field_validator("reviewer_decision")
    @classmethod
    def _validate_reviewer_decision(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        allowed = {"waived"}
        if value not in allowed:
            raise ValueError(
                f"Invalid reviewer decision. Allowed decisions: {', '.join(sorted(allowed))}"
            )
        return value


class AIReviewDecisionPatch(BaseModel):
    status: str
    decision_summary: str
    next_review_date: date | None = None
