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
    AIEvidenceItemOut,
    AIEvidencePatch,
    AIGovernanceReviewOut,
    AIImplementationPacketOut,
    AIReviewDecisionPatch,
    AIImpactAssessmentOut,
    AIInventorySummary,
    AILaunchGateOut,
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
    build_implementation_packets,
    build_launch_gate_payload,
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
    update_evidence_item,
    update_review_decision,
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


@router.get("/systems/{system_id}/launch-gate", response_model=AILaunchGateOut)
def system_launch_gate(
    system_id: uuid.UUID,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> AILaunchGateOut:
    payload = build_launch_gate_payload(db, org_id, system_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="AI system not found")
    return payload


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


@router.get(
    "/reviews/{review_id}/implementation-packets",
    response_model=list[AIImplementationPacketOut],
)
def review_implementation_packets(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> list[AIImplementationPacketOut]:
    packets = build_implementation_packets(db, org_id, review_id)
    if packets is None:
        raise HTTPException(status_code=404, detail="Governance review not found")
    return packets


@router.patch("/evidence/{evidence_id}", response_model=AIEvidenceItemOut)
def patch_evidence(
    evidence_id: uuid.UUID,
    payload: AIEvidencePatch,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> AIEvidenceItemOut:
    evidence = update_evidence_item(
        db,
        org_id,
        evidence_id,
        status=payload.status,
        evidence_uri=payload.evidence_uri,
        reviewer_decision=payload.reviewer_decision,
        reviewer_notes=payload.reviewer_notes,
        notes=payload.notes,
    )
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return evidence


@router.patch("/reviews/{review_id}/decision", response_model=AIGovernanceReviewOut)
def patch_review_decision(
    review_id: uuid.UUID,
    payload: AIReviewDecisionPatch,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(current_org),
) -> AIGovernanceReviewOut:
    try:
        review = update_review_decision(
            db,
            org_id,
            review_id,
            status=payload.status,
            decision_summary=payload.decision_summary,
            next_review_date=payload.next_review_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if review is None:
        raise HTTPException(status_code=404, detail="Governance review not found")
    return review


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
