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

APPROVAL_STATUSES = {"approved", "approved with conditions"}
EVIDENCE_READY_STATUSES = {"accepted"}
EVIDENCE_ALLOWED_STATUSES = {"missing", "provided", "accepted", "rejected"}


PACKET_TEMPLATES = {
    "risk assessment": {
        "source_framework": "NIST AI RMF / ISO/IEC 42001 A.5",
        "regulatory_driver": "Material AI risks must be identified, assessed, treated, and approved before launch.",
        "implementation_steps": [
            "Confirm the intended use, affected users, lifecycle stage, and residual risk.",
            "Map known harms, misuse paths, operational controls, and escalation owners.",
            "Record approval assumptions and open risks in the impact assessment.",
        ],
        "evidence_requirements": [
            "Completed impact assessment",
            "Risk treatment record",
            "Reviewer decision or residual-risk acceptance",
        ],
        "acceptance_criteria": [
            "Assessment covers the current system version and launch scope.",
            "Residual risk is approved by the named reviewer.",
            "Open risks have owners and review cadence.",
        ],
    },
    "data governance": {
        "source_framework": "EU AI Act high-risk controls / ISO/IEC 42001 A.7",
        "regulatory_driver": "Training, validation, test, input, and operational data must be fit for purpose and protected.",
        "implementation_steps": [
            "Document data sources, licenses, lineage, and transformation boundaries.",
            "Confirm customer data, prompts, and completions are excluded from provider training where required.",
            "Validate retention, access control, quality, bias, and representativeness checks.",
        ],
        "evidence_requirements": [
            "Data provenance record",
            "Training exclusion or retention attestation",
            "Data quality and protection review",
        ],
        "acceptance_criteria": [
            "Evidence identifies all regulated or sensitive data classes.",
            "Training and retention boundaries match the launch architecture.",
            "Reviewer accepts data quality and protection controls.",
        ],
    },
    "human oversight": {
        "source_framework": "EU AI Act Article 14 / ISO/IEC 42001 A.9.3",
        "regulatory_driver": "Human operators must be able to understand, supervise, override, and escalate AI outputs.",
        "implementation_steps": [
            "Assign accountable operators and reviewer roles.",
            "Document override, escalation, logging, and fallback procedures.",
            "Validate that users receive instructions for appropriate use and limitations.",
        ],
        "evidence_requirements": [
            "Human oversight procedure",
            "Operator instructions",
            "Escalation and override record",
        ],
        "acceptance_criteria": [
            "Named owners can intervene before harmful use or release.",
            "Override and escalation paths are tested or attested.",
            "Procedure aligns to the classified risk tier and role.",
        ],
    },
    "transparency notice": {
        "source_framework": "EU AI Act Article 50 / ISO/IEC 42001 A.8",
        "regulatory_driver": "People must receive clear notice when AI interaction, synthetic content, or other transparency-triggering uses apply.",
        "implementation_steps": [
            "Confirm whether direct interaction, biometric use, or synthetic content triggers notice obligations.",
            "Publish user-facing and customer-facing notice text for the launch scope.",
            "Link notice evidence to the Trust Center or product disclosure location.",
        ],
        "evidence_requirements": [
            "Transparency notice",
            "Content labeling or user disclosure",
            "Trust Center reference",
        ],
        "acceptance_criteria": [
            "Notice explains the AI use in plain operational terms.",
            "Disclosure is available before or during affected user interaction.",
            "Reviewer accepts the notice as aligned to classification answers.",
        ],
    },
    "medical ai validation": {
        "source_framework": "Medical AI validation / NIST AI RMF Measure",
        "regulatory_driver": "Medical AI systems require validation evidence before production use in regulated clinical workflows.",
        "implementation_steps": [
            "Lock validation protocol, dataset split strategy, and clinical representativeness assumptions.",
            "Review SOUP supplier documentation, model behavior risks, and human clinical override controls.",
            "Record validation results and post-market monitoring triggers.",
        ],
        "evidence_requirements": [
            "Clinical validation protocol and results",
            "SOUP supplier evidence",
            "Post-market monitoring plan",
        ],
        "acceptance_criteria": [
            "Validation protocol matches the intended medical workflow.",
            "Dataset split, leakage, and representativeness risks are addressed.",
            "Clinical owner accepts residual risk and monitoring plan.",
        ],
    },
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
    sync_trust_center_transparency(db, org_id, system, classification)
    db.commit()
    db.refresh(classification)
    return AIClassificationOut.model_validate(classification)


def build_launch_gate_payload(
    db: Session,
    org_id: uuid.UUID,
    ai_system_id: uuid.UUID,
):
    """Assemble the per-system launch gate workspace."""
    from app.schemas.ai_governance import (
        AIClassificationOut,
        AIComplianceTaskOut,
        AILaunchGateOut,
        AISystemOut,
        TrustTransparencyOut,
    )

    system = db.scalar(
        select(AISystemInventory)
        .where(AISystemInventory.id == ai_system_id, AISystemInventory.org_id == org_id)
        .options(selectinload(AISystemInventory.classifications))
    )
    if system is None:
        return None

    classification = latest_classification(system)
    transparency = (
        sync_trust_center_transparency(db, org_id, system, classification)
        if classification
        else None
    )

    task_rows = db.execute(
        select(AIComplianceTask, AISystemInventory.name)
        .join(AISystemInventory, AISystemInventory.id == AIComplianceTask.ai_system_id)
        .where(
            AIComplianceTask.org_id == org_id,
            AIComplianceTask.ai_system_id == system.id,
        )
        .order_by(AIComplianceTask.created_at)
    )
    tasks = [
        AIComplianceTaskOut.model_validate(task).model_copy(
            update={"system_name": system_name}
        )
        for task, system_name in task_rows
    ]

    guardrails = _guardrail_for_system(db, org_id, system)
    impact_assessment = _impact_assessment_for_system(db, org_id, system)
    review = _latest_review_for_system(db, org_id, system)
    evidence_items = _evidence_out(review.evidence_items if review else [])
    review_out = _review_out(review, system.name, evidence_items) if review else None
    readiness = _readiness(tasks, guardrails, review_out, evidence_items)

    system_out = AISystemOut.model_validate(system)
    system_out.latest_classification = (
        AIClassificationOut.model_validate(classification) if classification else None
    )

    db.flush()
    return AILaunchGateOut(
        system=system_out,
        latest_classification=system_out.latest_classification,
        tasks=tasks,
        guardrails=guardrails,
        impact_assessment=impact_assessment,
        governance_review=review_out,
        evidence_items=evidence_items,
        trust_center_transparency=(
            TrustTransparencyOut.model_validate(transparency) if transparency else None
        ),
        readiness=readiness,
    )


def build_implementation_packets(
    db: Session,
    org_id: uuid.UUID,
    review_id: uuid.UUID,
):
    """Return active implementation packets for incomplete review requirements."""
    from app.schemas.ai_governance import AIImplementationPacketOut

    review = db.scalar(
        select(AIGovernanceReview)
        .where(AIGovernanceReview.id == review_id, AIGovernanceReview.org_id == org_id)
        .options(
            selectinload(AIGovernanceReview.ai_system).selectinload(
                AISystemInventory.classifications
            ),
            selectinload(AIGovernanceReview.evidence_items),
        )
    )
    if review is None:
        return None

    system = review.ai_system
    classification = latest_classification(system)
    tasks = list(
        db.scalars(
            select(AIComplianceTask)
            .where(
                AIComplianceTask.org_id == org_id,
                AIComplianceTask.ai_system_id == system.id,
            )
            .order_by(AIComplianceTask.created_at)
        )
    )
    guardrails = _guardrail_for_system(db, org_id, system)
    impact_assessment = _impact_assessment_for_system(db, org_id, system)
    medical_risk = db.scalar(
        select(MedicalAIAlgorithmicRiskAssessment)
        .where(
            MedicalAIAlgorithmicRiskAssessment.org_id == org_id,
            MedicalAIAlgorithmicRiskAssessment.ai_system_id == system.id,
        )
        .order_by(MedicalAIAlgorithmicRiskAssessment.created_at.desc())
    )

    packets: list[AIImplementationPacketOut] = []
    for evidence in sorted(review.evidence_items, key=lambda item: item.requirement):
        if _evidence_launch_ready(evidence):
            continue
        template = _packet_template(
            evidence.requirement,
            classification=classification,
            tasks=tasks,
            guardrails=guardrails,
            impact_assessment=impact_assessment,
            medical_risk=medical_risk,
        )
        status = _packet_status(evidence)
        packets.append(
            AIImplementationPacketOut(
                id=f"packet-{evidence.id}",
                review_id=review.id,
                evidence_id=evidence.id,
                requirement_name=evidence.requirement,
                source_framework=template["source_framework"],
                regulatory_driver=template["regulatory_driver"],
                implementation_steps=template["implementation_steps"],
                evidence_requirements=template["evidence_requirements"],
                owner=evidence.owner or system.owner,
                due_date=review.next_review_date,
                review_cadence=_review_cadence(review),
                status=status,
                evidence_status=evidence.status,
                evidence_uri=evidence.evidence_uri,
                acceptance_criteria=template["acceptance_criteria"],
                current_evidence_title=evidence.title,
                reviewer_decision=evidence.reviewer_decision,
                reviewer_notes=evidence.reviewer_notes,
            )
        )
    return packets


def update_evidence_item(
    db: Session,
    org_id: uuid.UUID,
    evidence_id: uuid.UUID,
    *,
    status: str | None = None,
    evidence_uri: str | None = None,
    reviewer_decision: str | None = None,
    reviewer_notes: str | None = None,
    notes: str | None = None,
):
    """Update review evidence after checking tenant ownership and status validity."""
    from app.schemas.ai_governance import AIEvidenceItemOut

    if status is not None and status not in EVIDENCE_ALLOWED_STATUSES:
        raise ValueError("Invalid evidence status")
    if reviewer_decision not in {None, "", "waived"}:
        raise ValueError("Invalid reviewer decision")

    evidence = db.scalar(
        select(AIEvidenceItem)
        .join(AIGovernanceReview, AIGovernanceReview.id == AIEvidenceItem.review_id)
        .where(
            AIEvidenceItem.id == evidence_id,
            AIEvidenceItem.org_id == org_id,
            AIGovernanceReview.org_id == org_id,
        )
    )
    if evidence is None:
        return None

    if status is not None:
        evidence.status = status
    if evidence_uri is not None:
        evidence.evidence_uri = evidence_uri
    if reviewer_decision is not None:
        evidence.reviewer_decision = reviewer_decision
    if reviewer_notes is not None:
        evidence.reviewer_notes = reviewer_notes
    if notes is not None:
        evidence.notes = notes

    db.commit()
    db.refresh(evidence)
    return AIEvidenceItemOut.model_validate(evidence)


def update_review_decision(
    db: Session,
    org_id: uuid.UUID,
    review_id: uuid.UUID,
    *,
    status: str,
    decision_summary: str,
    next_review_date: date | None,
):
    """Update a governance review decision and enforce launch approval readiness."""
    review = db.scalar(
        select(AIGovernanceReview)
        .where(AIGovernanceReview.id == review_id, AIGovernanceReview.org_id == org_id)
        .options(selectinload(AIGovernanceReview.evidence_items))
    )
    if review is None:
        return None

    if status in APPROVAL_STATUSES:
        blockers = approval_blockers(review.evidence_items)
        if blockers:
            raise ValueError("; ".join(blockers))

    review.status = status
    review.decision_summary = decision_summary
    review.next_review_date = next_review_date

    system_name = db.scalar(
        select(AISystemInventory.name).where(
            AISystemInventory.id == review.ai_system_id,
            AISystemInventory.org_id == org_id,
        )
    ) or ""

    db.commit()
    db.refresh(review)
    return _review_out(review, system_name, _evidence_out(review.evidence_items))


def approval_blockers(evidence_items: list[AIEvidenceItem]) -> list[str]:
    """Return evidence blockers that prevent launch approval."""
    missing = [
        item.requirement
        for item in evidence_items
        if item.status == "missing" and not _evidence_launch_ready(item)
    ]
    provided = [
        item.requirement
        for item in evidence_items
        if item.status == "provided" and not _evidence_launch_ready(item)
    ]
    rejected = [
        item.requirement
        for item in evidence_items
        if item.status == "rejected" and not _evidence_launch_ready(item)
    ]
    blockers: list[str] = []
    if missing:
        blockers.append(f"Missing evidence: {', '.join(sorted(missing))}")
    if provided:
        blockers.append(f"Evidence awaiting acceptance: {', '.join(sorted(provided))}")
    if rejected:
        blockers.append(f"Rejected evidence: {', '.join(sorted(rejected))}")
    return blockers


def sync_trust_center_transparency(
    db: Session,
    org_id: uuid.UUID,
    system: AISystemInventory,
    classification: AIRiskClassification | None,
) -> TrustCenterAITransparencyMetric:
    """Create or update the public Trust Center AI transparency row."""
    answers = classification.questionnaire_answers if classification else {}
    direct_user_interaction = bool(answers.get("direct_user_interaction"))
    biometric_data = bool(answers.get("biometric_categorization_or_emotion"))
    synthetic_content = bool(answers.get("synthetic_content_or_deepfake"))
    deepfake_generation = bool(answers.get("synthetic_content_or_deepfake"))
    notice_required = direct_user_interaction or biometric_data or synthetic_content

    metric = db.scalar(
        select(TrustCenterAITransparencyMetric).where(
            TrustCenterAITransparencyMetric.org_id == org_id,
            TrustCenterAITransparencyMetric.ai_system_id == system.id,
        )
    )
    if metric is None:
        metric = db.scalar(
            select(TrustCenterAITransparencyMetric).where(
                TrustCenterAITransparencyMetric.org_id == org_id,
                TrustCenterAITransparencyMetric.system_name == system.name,
            )
        )
    if metric is None:
        metric = TrustCenterAITransparencyMetric(
            org_id=org_id,
            ai_system_id=system.id,
            system_name=system.name,
        )
        db.add(metric)

    metric.ai_system_id = system.id
    metric.system_name = system.name
    metric.direct_user_interaction = direct_user_interaction
    metric.biometric_data = biometric_data
    metric.synthetic_content = synthetic_content
    metric.deepfake_generation = deepfake_generation
    metric.eu_transparency_notice = "required" if notice_required else "not_required"
    metric.public_summary = system.business_purpose
    return metric


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
    from app.schemas.ai_governance import AIGovernanceReviewOut

    stmt = (
        select(AIGovernanceReview, AISystemInventory.name)
        .join(AISystemInventory, AISystemInventory.id == AIGovernanceReview.ai_system_id)
        .where(AIGovernanceReview.org_id == org_id)
        .options(selectinload(AIGovernanceReview.evidence_items))
        .order_by(AIGovernanceReview.next_review_date, AISystemInventory.name)
    )
    reviews: list[AIGovernanceReviewOut] = []
    for review, system_name in db.execute(stmt):
        reviews.append(_review_out(review, system_name, _evidence_out(review.evidence_items)))
    return reviews


def _packet_template(
    requirement: str,
    *,
    classification: AIRiskClassification | None,
    tasks: list[AIComplianceTask],
    guardrails,
    impact_assessment,
    medical_risk: MedicalAIAlgorithmicRiskAssessment | None,
):
    key = requirement.strip().lower()
    template = PACKET_TEMPLATES.get(
        key,
        {
            "source_framework": "AI governance launch gate",
            "regulatory_driver": "The requirement is part of the AI launch review and must be proven before approval.",
            "implementation_steps": [
                "Confirm the requirement owner and launch scope.",
                "Implement the control or process needed for the requirement.",
                "Attach evidence and route it to the reviewer for acceptance.",
            ],
            "evidence_requirements": [
                "Linked evidence URI",
                "Owner attestation",
                "Reviewer acceptance",
            ],
            "acceptance_criteria": [
                "Evidence matches the current system and launch scope.",
                "Owner and reviewer are recorded.",
                "Reviewer marks the evidence accepted or waives it with notes.",
            ],
        },
    )
    implementation_steps = list(template["implementation_steps"])
    evidence_requirements = list(template["evidence_requirements"])
    acceptance_criteria = list(template["acceptance_criteria"])

    if classification is not None:
        acceptance_criteria.append(
            f"Packet aligns to {classification.risk_tier} as {classification.actor_role}."
        )
    matching_task = _task_for_requirement(requirement, tasks)
    if matching_task is not None:
        implementation_steps.append(f"Close linked obligation: {matching_task.obligation}")
        evidence_requirements.extend(matching_task.evidence_required)
    if key == "data governance" and guardrails is not None:
        evidence_requirements.append("Privacy guardrail attestation")
    if key == "risk assessment" and impact_assessment is not None:
        evidence_requirements.append("NIST AI RMF impact assessment record")
    if key == "medical ai validation" and medical_risk is not None:
        evidence_requirements.append("Medical algorithmic risk assessment")

    return {
        "source_framework": template["source_framework"],
        "regulatory_driver": template["regulatory_driver"],
        "implementation_steps": _dedupe(implementation_steps),
        "evidence_requirements": _dedupe(evidence_requirements),
        "acceptance_criteria": _dedupe(acceptance_criteria),
    }


def _task_for_requirement(
    requirement: str, tasks: list[AIComplianceTask]
) -> AIComplianceTask | None:
    words = {word for word in requirement.lower().replace("-", " ").split() if word}
    for task in tasks:
        evidence_text = " ".join(task.evidence_required).lower()
        obligation_text = task.obligation.lower()
        if words and any(word in evidence_text or word in obligation_text for word in words):
            return task
    return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _review_cadence(review: AIGovernanceReview) -> str:
    if review.next_review_date is None:
        return "Before launch and on material change"
    return "By next review date and on material change"


def _packet_status(evidence: AIEvidenceItem) -> str:
    if evidence.reviewer_decision == "waived":
        return "waived"
    return evidence.status


def _evidence_launch_ready(evidence: AIEvidenceItem) -> bool:
    return evidence.status in EVIDENCE_READY_STATUSES or evidence.reviewer_decision == "waived"


def _evidence_out(evidence_items: list[AIEvidenceItem]):
    from app.schemas.ai_governance import AIEvidenceItemOut

    return [
        AIEvidenceItemOut.model_validate(item)
        for item in sorted(evidence_items, key=lambda item: item.requirement)
    ]


def _review_out(review: AIGovernanceReview, system_name: str, evidence):
    from app.schemas.ai_governance import AIGovernanceReviewOut

    ready = sum(1 for item in evidence if item.status == "accepted" or item.reviewer_decision == "waived")
    missing = sum(
        1
        for item in evidence
        if item.status == "missing" and item.reviewer_decision != "waived"
    )
    return AIGovernanceReviewOut.model_validate(review).model_copy(
        update={
            "system_name": system_name,
            "evidence_items": evidence,
            "evidence_ready": ready,
            "evidence_missing": missing,
        }
    )


def _latest_review_for_system(
    db: Session, org_id: uuid.UUID, system: AISystemInventory
) -> AIGovernanceReview | None:
    return db.scalar(
        select(AIGovernanceReview)
        .where(
            AIGovernanceReview.org_id == org_id,
            AIGovernanceReview.ai_system_id == system.id,
        )
        .options(selectinload(AIGovernanceReview.evidence_items))
        .order_by(AIGovernanceReview.created_at.desc())
    )


def _impact_assessment_for_system(db: Session, org_id: uuid.UUID, system: AISystemInventory):
    from app.schemas.ai_governance import AIImpactAssessmentOut

    impact = db.scalar(
        select(AIImpactAssessment)
        .where(
            AIImpactAssessment.org_id == org_id,
            AIImpactAssessment.ai_system_id == system.id,
        )
        .order_by(AIImpactAssessment.created_at.desc())
    )
    if impact is None:
        return None
    return AIImpactAssessmentOut.model_validate(impact).model_copy(
        update={"system_name": system.name}
    )


def _guardrail_for_system(db: Session, org_id: uuid.UUID, system: AISystemInventory):
    from app.schemas.ai_governance import GuardrailOut

    row = db.execute(
        select(AIDataPrivacyGuardrail, AIInfrastructureValidationCheck)
        .join(
            AIInfrastructureValidationCheck,
            AIInfrastructureValidationCheck.ai_system_id
            == AIDataPrivacyGuardrail.ai_system_id,
        )
        .where(
            AIDataPrivacyGuardrail.org_id == org_id,
            AIDataPrivacyGuardrail.ai_system_id == system.id,
            AIInfrastructureValidationCheck.org_id == org_id,
        )
    ).first()
    if row is None:
        return None
    privacy, infra = row
    return GuardrailOut(
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


def _readiness(tasks, guardrails, review, evidence_items):
    from app.schemas.ai_governance import LaunchGateReadiness

    evidence_total = len(evidence_items)
    evidence_ready = sum(
        1
        for item in evidence_items
        if item.status == "accepted" or item.reviewer_decision == "waived"
    )
    evidence_missing = sum(
        1
        for item in evidence_items
        if item.status == "missing" and item.reviewer_decision != "waived"
    )
    evidence_provided = sum(
        1
        for item in evidence_items
        if item.status == "provided" and item.reviewer_decision != "waived"
    )
    evidence_rejected = sum(
        1
        for item in evidence_items
        if item.status == "rejected" and item.reviewer_decision != "waived"
    )

    guardrail_checks = []
    if guardrails is not None:
        guardrail_checks = [
            guardrails.privacy_status == "passing",
            guardrails.infrastructure_status == "passing",
            guardrails.customer_data_training_blocked,
            guardrails.prompt_completion_training_blocked,
            guardrails.model_isolation_confirmed,
            guardrails.encryption_at_rest,
            guardrails.encryption_in_transit,
            guardrails.private_network_path,
        ]
    guardrails_total = len(guardrail_checks)
    guardrails_passing = sum(1 for passed in guardrail_checks if passed)

    task_done_statuses = {"done", "complete", "completed", "closed"}
    tasks_total = len(tasks)
    tasks_complete = sum(1 for task in tasks if task.status in task_done_statuses)

    review_status = review.status if review else ""
    review_points = 100 if review_status in APPROVAL_STATUSES else 60 if review else 0
    evidence_points = (
        round((evidence_ready / evidence_total) * 100) if evidence_total else 0
    )
    guardrail_points = (
        round((guardrails_passing / guardrails_total) * 100) if guardrails_total else 0
    )
    task_points = round((tasks_complete / tasks_total) * 100) if tasks_total else 100
    score = round(
        evidence_points * 0.45
        + guardrail_points * 0.25
        + task_points * 0.15
        + review_points * 0.15
    )

    blockers = []
    if evidence_missing:
        blockers.append("Missing evidence must be provided before approval.")
    if evidence_provided:
        blockers.append("Provided evidence must be accepted or waived before approval.")
    if evidence_rejected:
        blockers.append("Rejected evidence must be remediated before approval.")
    if guardrails_total and guardrails_passing < guardrails_total:
        blockers.append("All privacy and deployment guardrails must pass.")
    if review_status in APPROVAL_STATUSES:
        state = "approved"
    elif blockers:
        state = "blocked"
    elif evidence_total and evidence_ready == evidence_total:
        state = "ready"
    else:
        state = "in_review"

    return LaunchGateReadiness(
        score=score,
        state=state,
        evidence_ready=evidence_ready,
        evidence_total=evidence_total,
        evidence_missing=evidence_missing,
        evidence_rejected=evidence_rejected,
        guardrails_passing=guardrails_passing,
        guardrails_total=guardrails_total,
        tasks_complete=tasks_complete,
        tasks_total=tasks_total,
        approval_blockers=blockers,
    )


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
