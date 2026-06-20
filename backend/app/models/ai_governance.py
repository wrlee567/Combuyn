"""AI Governance ORM models.

This module extends the CCF-oriented GRC core with AI-specific inventory,
ISO/IEC 42001 Annex A control mapping, EU AI Act classification, NIST AI RMF
impact assessment, privacy/deployment guardrails, medical AI risk, and public
Trust Center transparency artifacts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.ccf import DEFAULT_ORG_ID
from app.models.types import JSONBType


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ISO42001ControlObjective(Base, TimestampMixin):
    """One of the nine ISO/IEC 42001 Annex A control objectives in scope."""

    __tablename__ = "iso42001_control_objectives"
    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_iso42001_objective_org_code"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    code: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")

    controls: Mapped[list["ISO42001AnnexAControl"]] = relationship(
        back_populates="objective",
        cascade="all, delete-orphan",
    )


class ISO42001AnnexAControl(Base, TimestampMixin):
    """AI-specific Annex A control selectable in the AIMS Statement of Applicability."""

    __tablename__ = "iso42001_annex_a_controls"
    __table_args__ = (
        UniqueConstraint("org_id", "control_id", name="uq_iso42001_control_org_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    objective_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("iso42001_control_objectives.id", ondelete="CASCADE"), index=True
    )

    control_id: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    implementation_guidance: Mapped[str] = mapped_column(Text, default="")
    audit_evidence: Mapped[str] = mapped_column(Text, default="")

    objective: Mapped[ISO42001ControlObjective] = relationship(back_populates="controls")
    system_mappings: Mapped[list["AISystemISOControlMapping"]] = relationship(
        back_populates="control",
        cascade="all, delete-orphan",
    )


class MedicalSOUPComponent(Base, TimestampMixin):
    """Medical Software of Unknown Provenance component tied to AI systems."""

    __tablename__ = "medical_soup_components"
    __table_args__ = (
        UniqueConstraint("org_id", "name", "version", name="uq_soup_component_version"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(128), default="")
    supplier: Mapped[str] = mapped_column(String(255), default="")
    intended_use: Mapped[str] = mapped_column(Text, default="")
    safety_class: Mapped[str] = mapped_column(String(64), default="unclassified")
    provenance_status: Mapped[str] = mapped_column(String(64), default="unknown")


class AISystemInventory(Base, TimestampMixin):
    """Inventory of internally developed and third-party AI systems."""

    __tablename__ = "ai_system_inventory"
    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_ai_system_inventory_org_name"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    name: Mapped[str] = mapped_column(String(255))
    owner: Mapped[str] = mapped_column(String(255), default="")
    business_purpose: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(64), default="internal")
    provider_name: Mapped[str] = mapped_column(String(255), default="")
    model_type: Mapped[str] = mapped_column(String(128), default="")
    foundation_model_used: Mapped[str] = mapped_column(String(255), default="")
    deployment_environment: Mapped[str] = mapped_column(String(128), default="private")
    lifecycle_stage: Mapped[str] = mapped_column(String(64), default="design")
    regulatory_role: Mapped[str] = mapped_column(String(64), default="Provider")
    eu_market: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_device_related: Mapped[bool] = mapped_column(Boolean, default=False)
    soup_component_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_soup_components.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_data_training_policy: Mapped[str] = mapped_column(
        String(255), default="blocked"
    )
    prompt_completion_training_policy: Mapped[str] = mapped_column(
        String(255), default="blocked"
    )
    data_classes: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)

    soup_component: Mapped[MedicalSOUPComponent | None] = relationship()
    iso_control_mappings: Mapped[list["AISystemISOControlMapping"]] = relationship(
        back_populates="ai_system",
        cascade="all, delete-orphan",
    )
    classifications: Mapped[list["AIRiskClassification"]] = relationship(
        back_populates="ai_system",
        cascade="all, delete-orphan",
    )
    impact_assessments: Mapped[list["AIImpactAssessment"]] = relationship(
        back_populates="ai_system",
        cascade="all, delete-orphan",
    )


class AISystemISOControlMapping(Base, TimestampMixin):
    """Join table mapping AI systems to ISO/IEC 42001 Annex A controls."""

    __tablename__ = "ai_system_iso_control_mappings"
    __table_args__ = (
        UniqueConstraint(
            "ai_system_id", "control_id", name="uq_ai_system_iso_control_mapping"
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    control_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("iso42001_annex_a_controls.id", ondelete="CASCADE"), index=True
    )
    applicability: Mapped[str] = mapped_column(String(64), default="applicable")
    status: Mapped[str] = mapped_column(String(64), default="planned")
    evidence_uri: Mapped[str] = mapped_column(String(512), default="")
    control_owner: Mapped[str] = mapped_column(String(255), default="")

    ai_system: Mapped[AISystemInventory] = relationship(back_populates="iso_control_mappings")
    control: Mapped[ISO42001AnnexAControl] = relationship(back_populates="system_mappings")


class AIRiskClassification(Base, TimestampMixin):
    """EU AI Act risk classification outcome and source questionnaire."""

    __tablename__ = "ai_risk_classifications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    actor_role: Mapped[str] = mapped_column(String(64), default="Provider")
    risk_tier: Mapped[str] = mapped_column(String(128))
    regulatory_scope: Mapped[str] = mapped_column(String(128), default="")
    questionnaire_version: Mapped[str] = mapped_column(
        String(64), default="eu-ai-act-15q-v1"
    )
    questionnaire_answers: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)
    rationale: Mapped[str] = mapped_column(Text, default="")

    ai_system: Mapped[AISystemInventory] = relationship(back_populates="classifications")
    tasks: Mapped[list["AIComplianceTask"]] = relationship(
        back_populates="classification",
        cascade="all, delete-orphan",
    )


class AIComplianceTask(Base, TimestampMixin):
    """Generated task tied to a risk tier and organizational AI Act role."""

    __tablename__ = "ai_compliance_tasks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    classification_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_risk_classifications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    framework: Mapped[str] = mapped_column(String(128), default="EU AI Act")
    obligation: Mapped[str] = mapped_column(Text)
    owner_role: Mapped[str] = mapped_column(String(64), default="Provider")
    status: Mapped[str] = mapped_column(String(64), default="open")
    due_offset_days: Mapped[int] = mapped_column(Integer, default=30)
    evidence_required: Mapped[list[str]] = mapped_column(JSONBType, default=list)

    classification: Mapped[AIRiskClassification | None] = relationship(back_populates="tasks")


class AIDataPrivacyGuardrail(Base, TimestampMixin):
    """Privacy boundary attestation for prompts, completions, and customer data."""

    __tablename__ = "ai_data_privacy_guardrails"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    customer_data_training_blocked: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_completion_training_blocked: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_policy: Mapped[str] = mapped_column(String(255), default="")
    pii_handling: Mapped[str] = mapped_column(Text, default="")
    boundary_evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(64), default="passing")


class AIInfrastructureValidationCheck(Base, TimestampMixin):
    """Private LLM deployment validation checks."""

    __tablename__ = "ai_infrastructure_validation_checks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    model_isolation_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_at_rest: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_in_transit: Mapped[bool] = mapped_column(Boolean, default=False)
    private_network_path: Mapped[bool] = mapped_column(Boolean, default=False)
    network_path_type: Mapped[str] = mapped_column(String(128), default="")
    validation_status: Mapped[str] = mapped_column(String(64), default="pending")


class AIVendorProvider(Base, TimestampMixin):
    """Third-party AI vendor onboarding and SBOM tracking."""

    __tablename__ = "ai_vendor_providers"
    __table_args__ = (
        UniqueConstraint("org_id", "name", "service", name="uq_ai_vendor_service"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    name: Mapped[str] = mapped_column(String(255))
    service: Mapped[str] = mapped_column(String(255), default="")
    onboarding_status: Mapped[str] = mapped_column(String(64), default="self-service vetting")
    sbom_received: Mapped[bool] = mapped_column(Boolean, default=False)
    sbom_format: Mapped[str] = mapped_column(String(64), default="")
    supply_chain_risk: Mapped[str] = mapped_column(String(64), default="unknown")
    data_processing_role: Mapped[str] = mapped_column(String(128), default="")
    evidence_uri: Mapped[str] = mapped_column(String(512), default="")


class AIImpactAssessment(Base, TimestampMixin):
    """NIST AI RMF Govern/Map/Measure/Manage impact assessment."""

    __tablename__ = "ai_impact_assessments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    lifecycle_stage: Mapped[str] = mapped_column(String(64), default="design")
    mandatory_review_status: Mapped[str] = mapped_column(String(64), default="required")
    nist_govern: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)
    nist_map: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)
    nist_measure: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)
    nist_manage: Mapped[dict[str, object]] = mapped_column(JSONBType, default=dict)
    data_provenance: Mapped[str] = mapped_column(Text, default="")
    data_quality: Mapped[str] = mapped_column(Text, default="")
    training_data_protections: Mapped[str] = mapped_column(Text, default="")
    residual_risk: Mapped[str] = mapped_column(String(64), default="medium")
    approval_status: Mapped[str] = mapped_column(String(64), default="draft")

    ai_system: Mapped[AISystemInventory] = relationship(back_populates="impact_assessments")


class AIGovernanceReview(Base, TimestampMixin):
    """Approval register entry for an AI system governance review."""

    __tablename__ = "ai_governance_reviews"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    review_name: Mapped[str] = mapped_column(String(255))
    review_type: Mapped[str] = mapped_column(String(128), default="pre-deployment")
    status: Mapped[str] = mapped_column(String(64), default="draft")
    risk_level: Mapped[str] = mapped_column(String(64), default="medium")
    reviewer: Mapped[str] = mapped_column(String(255), default="")
    decision_summary: Mapped[str] = mapped_column(Text, default="")
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    ai_system: Mapped[AISystemInventory] = relationship()
    evidence_items: Mapped[list["AIEvidenceItem"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class AIEvidenceItem(Base, TimestampMixin):
    """Evidence item tied to an AI governance review requirement."""

    __tablename__ = "ai_evidence_items"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_governance_reviews.id", ondelete="CASCADE"), index=True
    )
    requirement: Mapped[str] = mapped_column(String(255))
    evidence_type: Mapped[str] = mapped_column(String(128), default="document")
    title: Mapped[str] = mapped_column(String(255))
    evidence_uri: Mapped[str] = mapped_column(String(512), default="")
    owner: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(64), default="missing")
    notes: Mapped[str] = mapped_column(Text, default="")

    review: Mapped[AIGovernanceReview] = relationship(back_populates="evidence_items")


class MedicalAIAlgorithmicRiskAssessment(Base, TimestampMixin):
    """Medical AI risk assessment including dataset splits and model behavior risks."""

    __tablename__ = "medical_ai_algorithmic_risk_assessments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="CASCADE"), index=True
    )
    soup_component_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_soup_components.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    training_validation_test_split_risk: Mapped[str] = mapped_column(Text, default="")
    explainable_ai_evaluation: Mapped[str] = mapped_column(Text, default="")
    performative_prediction_risk: Mapped[str] = mapped_column(Text, default="")
    clinical_validation_status: Mapped[str] = mapped_column(String(64), default="pending")
    risk_controls: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(64), default="draft")


class TrustCenterFrameworkStatus(Base, TimestampMixin):
    """Public Trust Center framework status for continuous monitoring."""

    __tablename__ = "trust_center_framework_statuses"
    __table_args__ = (
        UniqueConstraint("org_id", "framework", name="uq_trust_center_framework"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    framework: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(64), default="monitored")
    coverage_percent: Mapped[int] = mapped_column(Integer, default=0)
    monitored_controls: Mapped[int] = mapped_column(Integer, default=0)
    public_summary: Mapped[str] = mapped_column(Text, default="")


class TrustCenterAITransparencyMetric(Base, TimestampMixin):
    """Public AI transparency flags mapped to EU AI Act notice obligations."""

    __tablename__ = "trust_center_ai_transparency_metrics"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    ai_system_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_system_inventory.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    system_name: Mapped[str] = mapped_column(String(255))
    direct_user_interaction: Mapped[bool] = mapped_column(Boolean, default=False)
    biometric_data: Mapped[bool] = mapped_column(Boolean, default=False)
    synthetic_content: Mapped[bool] = mapped_column(Boolean, default=False)
    deepfake_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    eu_transparency_notice: Mapped[str] = mapped_column(String(64), default="not_required")
    public_summary: Mapped[str] = mapped_column(Text, default="")


class TrustCenterDocumentRequest(Base, TimestampMixin):
    """Request workflow for sensitive trust documentation gated by NDA."""

    __tablename__ = "trust_center_document_requests"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    document_name: Mapped[str] = mapped_column(String(255))
    sensitivity: Mapped[str] = mapped_column(String(64), default="confidential")
    nda_required: Mapped[bool] = mapped_column(Boolean, default=True)
    nda_status: Mapped[str] = mapped_column(String(64), default="required")
    request_workflow: Mapped[str] = mapped_column(Text, default="")
    fulfillment_status: Mapped[str] = mapped_column(String(64), default="gated")
