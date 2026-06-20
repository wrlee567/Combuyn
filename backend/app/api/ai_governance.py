"""AI Governance API."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import current_org
from app.database import get_db
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
from app.schemas.ai_governance import (
    AIClassificationOut,
    AIClassificationRequest,
    AIComplianceTaskOut,
    AIEvidenceItemOut,
    AIGovernanceReviewOut,
    AIImpactAssessmentOut,
    AIInventorySummary,
    AISystemOut,
    ClassificationQuestionOut,
    GuardrailOut,
    ISO42001ControlOut,
    MedicalAIRiskOut,
    TrustCenterOut,
    TrustDocumentOut,
    TrustFrameworkOut,
    TrustTransparencyOut,
    VendorProviderOut,
)
from app.services.ai_governance import (
    EU_AI_ACT_QUESTIONNAIRE,
    classify_eu_ai_act,
    compliance_tasks_for,
)

router = APIRouter(
    prefix="/api/ai-governance",
    tags=["ai-governance"],
    dependencies=[Depends(current_org)],
)
# Public, unauthenticated: shows the platform's own (default-org) posture.
trust_router = APIRouter(prefix="/api/trust-center", tags=["trust-center"])


def _latest_classification(system: AISystemInventory) -> AIRiskClassification | None:
    if not system.classifications:
        return None
    return sorted(system.classifications, key=lambda c: c.created_at, reverse=True)[0]


@router.get("/summary", response_model=AIInventorySummary)
def summary(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> AIInventorySummary:
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
                AIGovernanceReview.next_review_date < date.today(),
                AIGovernanceReview.status != "retired",
            )
        )
        or 0,
    )


@router.get("/systems", response_model=list[AISystemOut])
def list_systems(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AISystemOut]:
    stmt = (
        select(AISystemInventory)
        .where(AISystemInventory.org_id == org_id)
        .options(selectinload(AISystemInventory.classifications))
        .order_by(AISystemInventory.name)
    )
    systems: list[AISystemOut] = []
    for system in db.scalars(stmt):
        out = AISystemOut.model_validate(system)
        latest = _latest_classification(system)
        out.latest_classification = (
            AIClassificationOut.model_validate(latest) if latest else None
        )
        systems.append(out)
    return systems


@router.get("/iso42001/controls", response_model=list[ISO42001ControlOut])
def list_iso42001_controls(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[ISO42001ControlOut]:
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


@router.get("/classification-questionnaire", response_model=list[ClassificationQuestionOut])
def classification_questionnaire() -> list[ClassificationQuestionOut]:
    return [ClassificationQuestionOut(**q) for q in EU_AI_ACT_QUESTIONNAIRE]


@router.post("/classifications", response_model=AIClassificationOut)
def classify_system(
    payload: AIClassificationRequest,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> AIClassificationOut:
    system = db.scalar(
        select(AISystemInventory).where(
            AISystemInventory.id == payload.ai_system_id,
            AISystemInventory.org_id == org_id,
        )
    )
    if system is None:
        raise HTTPException(status_code=404, detail="AI system not found")

    result = classify_eu_ai_act(payload.questionnaire_answers)
    classification = AIRiskClassification(
        ai_system_id=system.id,
        org_id=org_id,
        actor_role=payload.actor_role,
        risk_tier=result.risk_tier,
        regulatory_scope=result.regulatory_scope,
        questionnaire_answers=payload.questionnaire_answers,
        rationale=result.rationale,
    )
    db.add(classification)
    db.flush()

    for task_data in compliance_tasks_for(result.risk_tier, payload.actor_role):
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


@router.get("/tasks", response_model=list[AIComplianceTaskOut])
def list_tasks(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AIComplianceTaskOut]:
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


@router.get("/guardrails", response_model=list[GuardrailOut])
def list_guardrails(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[GuardrailOut]:
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


@router.get("/impact-assessments", response_model=list[AIImpactAssessmentOut])
def list_impact_assessments(
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> list[AIImpactAssessmentOut]:
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


@router.get("/reviews", response_model=list[AIGovernanceReviewOut])
def list_governance_reviews(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AIGovernanceReviewOut]:
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


@router.get("/medical-risk", response_model=list[MedicalAIRiskOut])
def list_medical_risk(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[MedicalAIRiskOut]:
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


@router.get("/vendors", response_model=list[VendorProviderOut])
def list_vendors(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[VendorProviderOut]:
    stmt = (
        select(AIVendorProvider)
        .where(AIVendorProvider.org_id == org_id)
        .order_by(AIVendorProvider.name)
    )
    return [VendorProviderOut.model_validate(v) for v in db.scalars(stmt)]


@trust_router.get("", response_model=TrustCenterOut)
def public_trust_center(db: Session = Depends(get_db)) -> TrustCenterOut:
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
