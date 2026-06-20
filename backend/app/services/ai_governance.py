"""AI governance workflow logic.

The service layer keeps regulatory decision logic out of the API router and
seed data. It intentionally returns transparent rationales so reviewers can
see why a system landed in an EU AI Act tier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.ccf import DEFAULT_ORG_ID
from app.models.ai_governance import (
    AIComplianceTask,
    AIDataPrivacyGuardrail,
    AIEvidenceItem,
    AIGovernanceReview,
    AIImpactAssessment,
    AIInfrastructureValidationCheck,
    AIRiskClassification,
    AISystemInventory,
    AIVendorProvider,
    ISO42001AnnexAControl,
    MedicalAIAlgorithmicRiskAssessment,
    MedicalSOUPComponent,
    TrustCenterAITransparencyMetric,
    TrustCenterDocumentRequest,
    TrustCenterFrameworkStatus,
)


EU_AI_ACT_QUESTIONNAIRE = [
    {
        "key": "ai_system",
        "text": "Does the capability meet the organization definition of an AI system?",
        "category": "scope",
    },
    {
        "key": "placed_on_eu_market",
        "text": "Is it placed on the EU market, used in the EU, or producing outputs used in the EU?",
        "category": "scope",
    },
    {
        "key": "subliminal_or_manipulative",
        "text": "Could it materially distort behavior through subliminal, deceptive, or manipulative techniques?",
        "category": "prohibited",
    },
    {
        "key": "exploits_vulnerabilities",
        "text": "Does it exploit vulnerabilities related to age, disability, or socioeconomic situation?",
        "category": "prohibited",
    },
    {
        "key": "social_scoring",
        "text": "Does it perform social scoring that leads to detrimental or unfavorable treatment?",
        "category": "prohibited",
    },
    {
        "key": "real_time_remote_biometric_identification",
        "text": "Does it enable real-time remote biometric identification in publicly accessible spaces?",
        "category": "prohibited",
    },
    {
        "key": "safety_component_or_regulated_product",
        "text": "Is it a safety component of a regulated product or a regulated product itself?",
        "category": "high_risk",
    },
    {
        "key": "medical_or_critical_infrastructure",
        "text": "Is it used for medical purposes, critical infrastructure, or other consequential safety contexts?",
        "category": "high_risk",
    },
    {
        "key": "education_employment_essential_services_law",
        "text": "Is it used for education, employment, essential services, law enforcement, migration, justice, or democratic processes?",
        "category": "high_risk",
    },
    {
        "key": "biometric_categorization_or_emotion",
        "text": "Does it perform biometric categorization or emotion recognition?",
        "category": "limited",
    },
    {
        "key": "direct_user_interaction",
        "text": "Does it interact directly with natural persons as an AI system?",
        "category": "limited",
    },
    {
        "key": "synthetic_content_or_deepfake",
        "text": "Does it generate or manipulate synthetic audio, image, video, or text content?",
        "category": "limited",
    },
    {
        "key": "general_purpose_model",
        "text": "Is it a general-purpose AI model or foundation model that can support multiple downstream uses?",
        "category": "gpai",
    },
    {
        "key": "systemic_risk_capability",
        "text": "Does the model have systemic-risk capability or broad downstream impact?",
        "category": "gpai",
    },
    {
        "key": "customer_data_used_for_training",
        "text": "Are customer data, prompts, or completions used to train or improve foundation models?",
        "category": "privacy",
    },
]


PROHIBITED_KEYS = {
    "subliminal_or_manipulative",
    "exploits_vulnerabilities",
    "social_scoring",
    "real_time_remote_biometric_identification",
}

HIGH_RISK_KEYS = {
    "safety_component_or_regulated_product",
    "medical_or_critical_infrastructure",
    "education_employment_essential_services_law",
}

LIMITED_RISK_KEYS = {
    "biometric_categorization_or_emotion",
    "direct_user_interaction",
    "synthetic_content_or_deepfake",
}


@dataclass(frozen=True)
class ClassificationResult:
    risk_tier: str
    regulatory_scope: str
    rationale: str


def _truthy(answers: dict[str, object], key: str) -> bool:
    return bool(answers.get(key))


def latest_classification(system: AISystemInventory) -> AIRiskClassification | None:
    """Return the newest classification already loaded on an AI system."""
    if not system.classifications:
        return None
    return sorted(system.classifications, key=lambda c: c.created_at, reverse=True)[0]


def build_ai_inventory_summary(
    db: Session, org_id: uuid.UUID, *, today: date | None = None
):
    """Return top-level AI governance counts for the dashboard."""
    from app.schemas.ai_governance import AIInventorySummary

    today = today or date.today()
    high_risk = db.scalar(
        select(func.count(AIRiskClassification.id)).where(
            AIRiskClassification.org_id == org_id,
            AIRiskClassification.risk_tier == "High-Risk Systems",
        )
    ) or 0
    gpai = db.scalar(
        select(func.count(AIRiskClassification.id)).where(
            AIRiskClassification.org_id == org_id,
            AIRiskClassification.risk_tier == "General Purpose AI (GPAI) Models",
        )
    ) or 0
    passing_privacy = db.scalar(
        select(func.count(AIDataPrivacyGuardrail.id)).where(
            AIDataPrivacyGuardrail.org_id == org_id,
            AIDataPrivacyGuardrail.status == "passing",
        )
    ) or 0
    passing_infra = db.scalar(
        select(func.count(AIInfrastructureValidationCheck.id)).where(
            AIInfrastructureValidationCheck.org_id == org_id,
            AIInfrastructureValidationCheck.validation_status == "passing",
        )
    ) or 0
    missing_evidence = db.scalar(
        select(func.count(AIEvidenceItem.id)).where(
            AIEvidenceItem.org_id == org_id, AIEvidenceItem.status == "missing"
        )
    ) or 0
    return AIInventorySummary(
        ai_systems=db.scalar(
            select(func.count(AISystemInventory.id)).where(
                AISystemInventory.org_id == org_id
            )
        )
        or 0,
        iso42001_controls=db.scalar(
            select(func.count(ISO42001AnnexAControl.id)).where(
                ISO42001AnnexAControl.org_id == org_id
            )
        )
        or 0,
        high_risk_systems=high_risk,
        gpai_systems=gpai,
        open_tasks=db.scalar(
            select(func.count(AIComplianceTask.id)).where(
                AIComplianceTask.org_id == org_id, AIComplianceTask.status == "open"
            )
        )
        or 0,
        passing_guardrails=passing_privacy + passing_infra,
        trust_center_frameworks=db.scalar(
            select(func.count(TrustCenterFrameworkStatus.id)).where(
                TrustCenterFrameworkStatus.org_id == org_id
            )
        )
        or 0,
        evidence_items=db.scalar(
            select(func.count(AIEvidenceItem.id)).where(
                AIEvidenceItem.org_id == org_id
            )
        )
        or 0,
        missing_evidence=missing_evidence,
        overdue_reviews=db.scalar(
            select(func.count(AIGovernanceReview.id)).where(
                AIGovernanceReview.org_id == org_id,
                AIGovernanceReview.next_review_date < today,
                AIGovernanceReview.status != "retired",
            )
        )
        or 0,
    )


def list_ai_systems(db: Session, org_id: uuid.UUID):
    """List AI systems with their latest loaded classification."""
    from app.schemas.ai_governance import AIClassificationOut, AISystemOut

    stmt = (
        select(AISystemInventory)
        .where(AISystemInventory.org_id == org_id)
        .options(selectinload(AISystemInventory.classifications))
        .order_by(AISystemInventory.name)
    )
    systems: list[AISystemOut] = []
    for system in db.scalars(stmt):
        out = AISystemOut.model_validate(system)
        latest = latest_classification(system)
        out.latest_classification = (
            AIClassificationOut.model_validate(latest) if latest else None
        )
        systems.append(out)
    return systems


def list_iso42001_controls(db: Session, org_id: uuid.UUID):
    """List ISO/IEC 42001 controls with objective metadata flattened."""
    from app.schemas.ai_governance import ISO42001ControlOut

    stmt = (
        select(ISO42001AnnexAControl)
        .where(ISO42001AnnexAControl.org_id == org_id)
        .options(selectinload(ISO42001AnnexAControl.objective))
        .order_by(ISO42001AnnexAControl.control_id)
    )
    controls: list[ISO42001ControlOut] = []
    for control in db.scalars(stmt):
        controls.append(
            ISO42001ControlOut(
                id=control.id,
                objective_code=control.objective.code,
                objective_title=control.objective.title,
                control_id=control.control_id,
                title=control.title,
                description=control.description,
                implementation_guidance=control.implementation_guidance,
                audit_evidence=control.audit_evidence,
            )
        )
    return controls


def create_classification_for_system(
    db: Session,
    org_id: uuid.UUID,
    *,
    ai_system_id: uuid.UUID,
    actor_role: str,
    questionnaire_answers: dict[str, object],
):
    """Classify an owned AI system and generate its compliance tasks."""
    from app.schemas.ai_governance import AIClassificationOut

    system = db.scalar(
        select(AISystemInventory).where(
            AISystemInventory.id == ai_system_id,
            AISystemInventory.org_id == org_id,
        )
    )
    if system is None:
        return None

    result = classify_eu_ai_act(questionnaire_answers)
    classification = AIRiskClassification(
        ai_system_id=system.id,
        org_id=org_id,
        actor_role=actor_role,
        risk_tier=result.risk_tier,
        regulatory_scope=result.regulatory_scope,
        questionnaire_answers=questionnaire_answers,
        rationale=result.rationale,
    )
    db.add(classification)
    db.flush()

    for task_data in compliance_tasks_for(result.risk_tier, actor_role):
        db.add(
            AIComplianceTask(
                ai_system_id=system.id,
                org_id=org_id,
                classification_id=classification.id,
                **task_data,
            )
        )
    db.commit()
    db.refresh(classification)
    return AIClassificationOut.model_validate(classification)


def list_ai_compliance_tasks(db: Session, org_id: uuid.UUID):
    """List generated AI compliance tasks with system names."""
    from app.schemas.ai_governance import AIComplianceTaskOut

    stmt = (
        select(AIComplianceTask, AISystemInventory.name)
        .join(AISystemInventory, AISystemInventory.id == AIComplianceTask.ai_system_id)
        .where(AIComplianceTask.org_id == org_id)
        .order_by(AIComplianceTask.created_at.desc())
    )
    return [
        AIComplianceTaskOut.model_validate(task).model_copy(
            update={"system_name": system_name}
        )
        for task, system_name in db.execute(stmt)
    ]


def list_ai_guardrails(db: Session, org_id: uuid.UUID):
    """List privacy and infrastructure guardrails by system."""
    from app.schemas.ai_governance import GuardrailOut

    stmt = (
        select(AISystemInventory, AIDataPrivacyGuardrail, AIInfrastructureValidationCheck)
        .join(
            AIDataPrivacyGuardrail,
            AIDataPrivacyGuardrail.ai_system_id == AISystemInventory.id,
        )
        .join(
            AIInfrastructureValidationCheck,
            AIInfrastructureValidationCheck.ai_system_id == AISystemInventory.id,
        )
        .where(AISystemInventory.org_id == org_id)
        .order_by(AISystemInventory.name)
    )
    return [
        GuardrailOut(
            ai_system_id=system.id,
            system_name=system.name,
            privacy_status=privacy.status,
            customer_data_training_blocked=privacy.customer_data_training_blocked,
            prompt_completion_training_blocked=privacy.prompt_completion_training_blocked,
            retention_policy=privacy.retention_policy,
            infrastructure_status=infra.validation_status,
            model_isolation_confirmed=infra.model_isolation_confirmed,
            encryption_at_rest=infra.encryption_at_rest,
            encryption_in_transit=infra.encryption_in_transit,
            private_network_path=infra.private_network_path,
            network_path_type=infra.network_path_type,
        )
        for system, privacy, infra in db.execute(stmt)
    ]


def list_ai_impact_assessments(db: Session, org_id: uuid.UUID):
    """List NIST AI RMF impact assessments with system names."""
    from app.schemas.ai_governance import AIImpactAssessmentOut

    stmt = (
        select(AIImpactAssessment, AISystemInventory.name)
        .join(AISystemInventory, AISystemInventory.id == AIImpactAssessment.ai_system_id)
        .where(AIImpactAssessment.org_id == org_id)
        .order_by(AISystemInventory.name)
    )
    return [
        AIImpactAssessmentOut.model_validate(assessment).model_copy(
            update={"system_name": system_name}
        )
        for assessment, system_name in db.execute(stmt)
    ]


def list_ai_governance_reviews(db: Session, org_id: uuid.UUID):
    """List governance reviews with sorted evidence and readiness counts."""
    from app.schemas.ai_governance import AIEvidenceItemOut, AIGovernanceReviewOut

    stmt = (
        select(AIGovernanceReview, AISystemInventory.name)
        .join(AISystemInventory, AISystemInventory.id == AIGovernanceReview.ai_system_id)
        .where(AIGovernanceReview.org_id == org_id)
        .options(selectinload(AIGovernanceReview.evidence_items))
        .order_by(AIGovernanceReview.next_review_date, AISystemInventory.name)
    )
    reviews: list[AIGovernanceReviewOut] = []
    for review, system_name in db.execute(stmt):
        evidence = [
            AIEvidenceItemOut.model_validate(item)
            for item in sorted(review.evidence_items, key=lambda item: item.requirement)
        ]
        ready = sum(1 for item in evidence if item.status in {"accepted", "provided"})
        missing = sum(1 for item in evidence if item.status == "missing")
        reviews.append(
            AIGovernanceReviewOut.model_validate(review).model_copy(
                update={
                    "system_name": system_name,
                    "evidence_items": evidence,
                    "evidence_ready": ready,
                    "evidence_missing": missing,
                }
            )
        )
    return reviews


def list_medical_ai_risks(db: Session, org_id: uuid.UUID):
    """List medical AI risk assessments with system and SOUP names."""
    from app.schemas.ai_governance import MedicalAIRiskOut

    stmt = (
        select(
            MedicalAIAlgorithmicRiskAssessment,
            AISystemInventory.name,
            MedicalSOUPComponent.name,
        )
        .join(
            AISystemInventory,
            AISystemInventory.id == MedicalAIAlgorithmicRiskAssessment.ai_system_id,
        )
        .join(
            MedicalSOUPComponent,
            MedicalSOUPComponent.id
            == MedicalAIAlgorithmicRiskAssessment.soup_component_id,
            isouter=True,
        )
        .where(MedicalAIAlgorithmicRiskAssessment.org_id == org_id)
        .order_by(AISystemInventory.name)
    )
    return [
        MedicalAIRiskOut.model_validate(risk).model_copy(
            update={"system_name": system_name, "soup_component": soup_name or ""}
        )
        for risk, system_name, soup_name in db.execute(stmt)
    ]


def list_ai_vendor_providers(db: Session, org_id: uuid.UUID):
    """List third-party AI vendor providers."""
    from app.schemas.ai_governance import VendorProviderOut

    stmt = (
        select(AIVendorProvider)
        .where(AIVendorProvider.org_id == org_id)
        .order_by(AIVendorProvider.name)
    )
    return [VendorProviderOut.model_validate(v) for v in db.scalars(stmt)]


def build_public_trust_center(db: Session):
    """Return the public default-org Trust Center AI posture."""
    from app.schemas.ai_governance import (
        TrustCenterOut,
        TrustDocumentOut,
        TrustFrameworkOut,
        TrustTransparencyOut,
    )

    frameworks = [
        TrustFrameworkOut.model_validate(f)
        for f in db.scalars(
            select(TrustCenterFrameworkStatus)
            .where(TrustCenterFrameworkStatus.org_id == DEFAULT_ORG_ID)
            .order_by(TrustCenterFrameworkStatus.framework)
        )
    ]
    transparency = [
        TrustTransparencyOut.model_validate(t)
        for t in db.scalars(
            select(TrustCenterAITransparencyMetric)
            .where(TrustCenterAITransparencyMetric.org_id == DEFAULT_ORG_ID)
            .order_by(TrustCenterAITransparencyMetric.system_name)
        )
    ]
    documents = [
        TrustDocumentOut.model_validate(d)
        for d in db.scalars(
            select(TrustCenterDocumentRequest)
            .where(TrustCenterDocumentRequest.org_id == DEFAULT_ORG_ID)
            .order_by(TrustCenterDocumentRequest.document_name)
        )
    ]
    return TrustCenterOut(
        frameworks=frameworks,
        ai_transparency=transparency,
        documents=documents,
    )


def classify_eu_ai_act(answers: dict[str, object]) -> ClassificationResult:
    """Classify an AI system into the EU AI Act risk tier taxonomy."""
    if not _truthy(answers, "ai_system"):
        return ClassificationResult(
            risk_tier="Out of Scope",
            regulatory_scope="not_ai_system",
            rationale="The questionnaire indicates this capability is not an AI system.",
        )

    if not _truthy(answers, "placed_on_eu_market"):
        return ClassificationResult(
            risk_tier="Minimal Risk Systems",
            regulatory_scope="non_eu_operational_scope",
            rationale="The system is tracked in inventory, but EU market/use scope is not indicated.",
        )

    matched_prohibited = sorted(k for k in PROHIBITED_KEYS if _truthy(answers, k))
    if matched_prohibited:
        return ClassificationResult(
            risk_tier="Prohibited Practices (Unacceptable Risk)",
            regulatory_scope="prohibited_practice",
            rationale=f"Prohibited-practice indicators were selected: {', '.join(matched_prohibited)}.",
        )

    matched_high = sorted(k for k in HIGH_RISK_KEYS if _truthy(answers, k))
    if matched_high:
        return ClassificationResult(
            risk_tier="High-Risk Systems",
            regulatory_scope="high_risk_ai_system",
            rationale=f"High-risk Annex/category indicators were selected: {', '.join(matched_high)}.",
        )

    if _truthy(answers, "general_purpose_model"):
        scope = "gpai_with_systemic_risk" if _truthy(answers, "systemic_risk_capability") else "gpai_model"
        return ClassificationResult(
            risk_tier="General Purpose AI (GPAI) Models",
            regulatory_scope=scope,
            rationale="The system is a general-purpose or foundation model.",
        )

    matched_limited = sorted(k for k in LIMITED_RISK_KEYS if _truthy(answers, k))
    if matched_limited:
        return ClassificationResult(
            risk_tier="Limited Risk Systems",
            regulatory_scope="transparency_obligations",
            rationale=f"Transparency-triggering indicators were selected: {', '.join(matched_limited)}.",
        )

    return ClassificationResult(
        risk_tier="Minimal Risk Systems",
        regulatory_scope="inventory_only",
        rationale="No prohibited, high-risk, GPAI, or limited-risk indicators were selected.",
    )


def compliance_tasks_for(risk_tier: str, actor_role: str) -> list[dict[str, object]]:
    """Return role-specific tasks for the classification outcome."""
    role = actor_role.lower()
    tasks: list[dict[str, object]] = []

    def add(obligation: str, days: int, evidence: list[str]) -> None:
        tasks.append(
            {
                "framework": "EU AI Act",
                "obligation": obligation,
                "owner_role": actor_role,
                "due_offset_days": days,
                "evidence_required": evidence,
                "status": "open",
            }
        )

    if risk_tier == "Prohibited Practices (Unacceptable Risk)":
        add(
            "Escalate to AI governance council and block deployment until legal review is complete.",
            7,
            ["legal assessment", "deployment hold evidence", "executive decision record"],
        )
        return tasks

    if risk_tier == "High-Risk Systems":
        if role == "provider":
            add("Maintain a documented risk management system.", 30, ["risk register", "risk controls"])
            add("Document training, validation, and test data governance.", 30, ["data governance file"])
            add("Prepare technical documentation and instructions for use.", 45, ["technical file"])
            add("Implement logging, human oversight, accuracy, robustness, and cybersecurity controls.", 45, ["test reports"])
            add("Plan conformity assessment and post-market monitoring.", 60, ["assessment plan", "monitoring plan"])
        elif role == "deployer":
            add("Use the system according to provider instructions and maintain human oversight.", 30, ["use procedure"])
            add("Confirm input data relevance and retain operating logs.", 30, ["input data review", "logs"])
            add("Complete impact/fundamental-rights assessment where required.", 45, ["impact assessment"])
        elif role in {"importer", "distributor"}:
            add("Verify provider conformity documentation, CE marking where applicable, and instructions for use.", 30, ["provider declaration", "traceability record"])
            add("Stop supply or escalation when non-conformity is suspected.", 15, ["non-conformity workflow"])
        else:
            add("Assign EU AI Act role and owner before deployment.", 14, ["role assignment"])
    elif risk_tier == "General Purpose AI (GPAI) Models":
        if role == "provider":
            add("Maintain GPAI technical documentation for downstream providers.", 45, ["model card", "technical documentation"])
            add("Publish copyright policy and training-content summary.", 45, ["copyright policy", "training summary"])
            add("Evaluate and mitigate systemic risks where applicable.", 60, ["model evaluation", "red-team report"])
        else:
            add("Collect provider GPAI documentation and verify downstream-use boundaries.", 30, ["vendor documentation", "use-case review"])
            add("Document prompt, completion, and customer-data training exclusions.", 30, ["privacy guardrail attestation"])
    elif risk_tier == "Limited Risk Systems":
        add("Publish transparency notice for user interaction, biometric use, or synthetic content.", 30, ["user notice", "content labeling"])
    elif risk_tier == "Minimal Risk Systems":
        add("Keep the system in inventory and re-review on material change.", 90, ["inventory review"])

    return tasks
