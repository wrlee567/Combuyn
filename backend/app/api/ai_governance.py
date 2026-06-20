"""AI Governance API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_org
from app.database import get_db
from app.schemas.ai_governance import (
    AIClassificationOut,
    AIClassificationRequest,
    AIComplianceTaskOut,
    AIGovernanceReviewOut,
    AIImpactAssessmentOut,
    AIInventorySummary,
    AISystemOut,
    ClassificationQuestionOut,
    GuardrailOut,
    ISO42001ControlOut,
    MedicalAIRiskOut,
    TrustCenterOut,
    VendorProviderOut,
)
from app.services.ai_governance import (
    EU_AI_ACT_QUESTIONNAIRE,
    build_ai_inventory_summary,
    build_public_trust_center,
    create_classification_for_system,
    list_ai_compliance_tasks,
    list_ai_governance_reviews,
    list_ai_guardrails,
    list_ai_impact_assessments,
    list_ai_systems,
    list_ai_vendor_providers,
    list_iso42001_controls as list_iso42001_control_catalog,
    list_medical_ai_risks,
)

router = APIRouter(
    prefix="/api/ai-governance",
    tags=["ai-governance"],
    dependencies=[Depends(current_org)],
)
# Public, unauthenticated: shows the platform's own (default-org) posture.
trust_router = APIRouter(prefix="/api/trust-center", tags=["trust-center"])


@router.get("/summary", response_model=AIInventorySummary)
def summary(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> AIInventorySummary:
    return build_ai_inventory_summary(db, org_id)


@router.get("/systems", response_model=list[AISystemOut])
def list_systems(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AISystemOut]:
    return list_ai_systems(db, org_id)


@router.get("/iso42001/controls", response_model=list[ISO42001ControlOut])
def list_iso42001_controls(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[ISO42001ControlOut]:
    return list_iso42001_control_catalog(db, org_id)


@router.get("/classification-questionnaire", response_model=list[ClassificationQuestionOut])
def classification_questionnaire() -> list[ClassificationQuestionOut]:
    return [ClassificationQuestionOut(**q) for q in EU_AI_ACT_QUESTIONNAIRE]


@router.post("/classifications", response_model=AIClassificationOut)
def classify_system(
    payload: AIClassificationRequest,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> AIClassificationOut:
    classification = create_classification_for_system(
        db,
        org_id,
        ai_system_id=payload.ai_system_id,
        actor_role=payload.actor_role,
        questionnaire_answers=payload.questionnaire_answers,
    )
    if classification is None:
        raise HTTPException(status_code=404, detail="AI system not found")
    return classification


@router.get("/tasks", response_model=list[AIComplianceTaskOut])
def list_tasks(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AIComplianceTaskOut]:
    return list_ai_compliance_tasks(db, org_id)


@router.get("/guardrails", response_model=list[GuardrailOut])
def list_guardrails(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[GuardrailOut]:
    return list_ai_guardrails(db, org_id)


@router.get("/impact-assessments", response_model=list[AIImpactAssessmentOut])
def list_impact_assessments(
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> list[AIImpactAssessmentOut]:
    return list_ai_impact_assessments(db, org_id)


@router.get("/reviews", response_model=list[AIGovernanceReviewOut])
def list_governance_reviews(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[AIGovernanceReviewOut]:
    return list_ai_governance_reviews(db, org_id)


@router.get("/medical-risk", response_model=list[MedicalAIRiskOut])
def list_medical_risk(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[MedicalAIRiskOut]:
    return list_medical_ai_risks(db, org_id)


@router.get("/vendors", response_model=list[VendorProviderOut])
def list_vendors(
    db: Session = Depends(get_db), org_id: uuid.UUID = Depends(current_org)
) -> list[VendorProviderOut]:
    return list_ai_vendor_providers(db, org_id)


@trust_router.get("", response_model=TrustCenterOut)
def public_trust_center(db: Session = Depends(get_db)) -> TrustCenterOut:
    return build_public_trust_center(db)
