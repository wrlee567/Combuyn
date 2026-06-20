"""Idempotent seeding for AI Governance reference and demo data."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_governance import (
    AIComplianceTask,
    AIDataPrivacyGuardrail,
    AIEvidenceItem,
    AIGovernanceReview,
    AIImpactAssessment,
    AIInfrastructureValidationCheck,
    AIRiskClassification,
    AISystemInventory,
    AISystemISOControlMapping,
    AIVendorProvider,
    ISO42001AnnexAControl,
    ISO42001ControlObjective,
    MedicalAIAlgorithmicRiskAssessment,
    MedicalSOUPComponent,
    TrustCenterAITransparencyMetric,
    TrustCenterDocumentRequest,
    TrustCenterFrameworkStatus,
)
from app.seed.ai_governance_reference import (
    ISO42001_CONTROLS,
    ISO42001_OBJECTIVES,
    SAMPLE_AI_SYSTEMS,
    TRUST_CENTER_FRAMEWORKS,
    VENDORS,
)
from app.services.ai_governance import classify_eu_ai_act, compliance_tasks_for


def seed_ai_reference(db: Session) -> dict[str, int]:
    """Seed the immutable ISO 42001 Annex A catalog (objectives + controls).

    This is standards reference data and is safe to seed in production.
    """
    created = {"iso_objectives": 0, "iso_controls": 0}

    objective_by_code: dict[str, ISO42001ControlObjective] = {}
    for code, title, description in ISO42001_OBJECTIVES:
        objective = db.scalar(
            select(ISO42001ControlObjective).where(
                ISO42001ControlObjective.code == code
            )
        )
        if objective is None:
            objective = ISO42001ControlObjective(
                code=code,
                title=title,
                description=description,
            )
            db.add(objective)
            db.flush()
            created["iso_objectives"] += 1
        objective_by_code[code] = objective

    control_by_id: dict[str, ISO42001AnnexAControl] = {}
    for objective_code, control_id, title, description in ISO42001_CONTROLS:
        control = db.scalar(
            select(ISO42001AnnexAControl).where(
                ISO42001AnnexAControl.control_id == control_id
            )
        )
        if control is None:
            control = ISO42001AnnexAControl(
                objective_id=objective_by_code[objective_code].id,
                control_id=control_id,
                title=title,
                description=description,
                implementation_guidance=f"Assign an owner, evidence source, and review cadence for {control_id}.",
                audit_evidence="Policy, procedure, review record, technical evidence, or system attestation.",
            )
            db.add(control)
            db.flush()
            created["iso_controls"] += 1
        control_by_id[control_id] = control

    db.commit()
    return created


def seed_ai_demo(db: Session) -> dict[str, int]:
    """Seed illustrative AI systems, classifications, guardrails, governance
    reviews, vendors, and trust-center records.

    This is sample/demo data and MUST NOT be seeded in production.
    Depends on :func:`seed_ai_reference` having populated the ISO 42001 catalog.
    """
    created = {
        "ai_systems": 0,
        "classifications": 0,
        "tasks": 0,
        "guardrails": 0,
        "governance_reviews": 0,
        "evidence_items": 0,
        "impact_assessments": 0,
        "medical_risks": 0,
        "vendors": 0,
        "trust_center": 0,
    }

    control_by_id: dict[str, ISO42001AnnexAControl] = {
        c.control_id: c for c in db.scalars(select(ISO42001AnnexAControl))
    }

    soup_component = db.scalar(
        select(MedicalSOUPComponent).where(
            MedicalSOUPComponent.name == "ClinicalAI Vendor Scoring Engine"
        )
    )
    if soup_component is None:
        soup_component = MedicalSOUPComponent(
            name="ClinicalAI Vendor Scoring Engine",
            version="2026.06",
            supplier="ClinicalAI Vendor",
            intended_use="Medical triage risk scoring for clinician review.",
            safety_class="medical-ai-soup",
            provenance_status="supplier attestation required",
        )
        db.add(soup_component)
        db.flush()

    for vendor in VENDORS:
        exists = db.scalar(
            select(AIVendorProvider).where(
                AIVendorProvider.name == vendor["name"],
                AIVendorProvider.service == vendor["service"],
            )
        )
        if exists is None:
            db.add(AIVendorProvider(**vendor))
            created["vendors"] += 1

    lifecycle_controls = [
        "A.2.1",
        "A.3.1",
        "A.5.1",
        "A.6.1",
        "A.6.3",
        "A.6.4",
        "A.6.5",
        "A.7.3",
        "A.7.4",
        "A.8.2",
        "A.10.2",
    ]

    for data in SAMPLE_AI_SYSTEMS:
        system_data = dict(data)
        answers = system_data.pop("classification_answers")
        system = db.scalar(
            select(AISystemInventory).where(AISystemInventory.name == system_data["name"])
        )
        if system is None:
            soup_id = soup_component.id if system_data["medical_device_related"] else None
            system = AISystemInventory(**system_data, soup_component_id=soup_id)
            db.add(system)
            db.flush()
            created["ai_systems"] += 1

        for control_id in lifecycle_controls:
            control = control_by_id[control_id]
            exists = db.scalar(
                select(AISystemISOControlMapping).where(
                    AISystemISOControlMapping.ai_system_id == system.id,
                    AISystemISOControlMapping.control_id == control.id,
                )
            )
            if exists is None:
                db.add(
                    AISystemISOControlMapping(
                        ai_system_id=system.id,
                        control_id=control.id,
                        status="implemented" if system.lifecycle_stage == "deployed" else "in progress",
                        control_owner=system.owner,
                        evidence_uri=f"trust://ai-systems/{system.name.lower().replace(' ', '-')}/{control_id}",
                    )
                )

        classification = db.scalar(
            select(AIRiskClassification).where(
                AIRiskClassification.ai_system_id == system.id
            )
        )
        if classification is None:
            result = classify_eu_ai_act(answers)
            classification = AIRiskClassification(
                ai_system_id=system.id,
                actor_role=system.regulatory_role,
                risk_tier=result.risk_tier,
                regulatory_scope=result.regulatory_scope,
                questionnaire_answers=answers,
                rationale=result.rationale,
            )
            db.add(classification)
            db.flush()
            created["classifications"] += 1

            for task_data in compliance_tasks_for(result.risk_tier, system.regulatory_role):
                db.add(
                    AIComplianceTask(
                        ai_system_id=system.id,
                        classification_id=classification.id,
                        **task_data,
                    )
                )
                created["tasks"] += 1

        if not db.scalar(
            select(AIDataPrivacyGuardrail).where(
                AIDataPrivacyGuardrail.ai_system_id == system.id
            )
        ):
            db.add(
                AIDataPrivacyGuardrail(
                    ai_system_id=system.id,
                    customer_data_training_blocked=True,
                    prompt_completion_training_blocked=True,
                    retention_policy="Zero retention for prompts/completions unless explicit enterprise retention is configured.",
                    pii_handling="Sensitive data is minimized, access-controlled, encrypted, and excluded from provider training.",
                    boundary_evidence="Provider contract, architecture review, and gateway policy confirm training exclusion.",
                    status="passing",
                )
            )
            created["guardrails"] += 1

        if not db.scalar(
            select(AIInfrastructureValidationCheck).where(
                AIInfrastructureValidationCheck.ai_system_id == system.id
            )
        ):
            private_path = system.deployment_environment in {"private VPC", "private endpoint"}
            db.add(
                AIInfrastructureValidationCheck(
                    ai_system_id=system.id,
                    model_isolation_confirmed=True,
                    encryption_at_rest=True,
                    encryption_in_transit=True,
                    private_network_path=private_path,
                    network_path_type="VPC PrivateLink" if private_path else "public TLS",
                    validation_status="passing" if private_path else "review",
                )
            )
            created["guardrails"] += 1

        if not db.scalar(
            select(AIImpactAssessment).where(AIImpactAssessment.ai_system_id == system.id)
        ):
            db.add(
                AIImpactAssessment(
                    ai_system_id=system.id,
                    lifecycle_stage=system.lifecycle_stage,
                    mandatory_review_status="required before production"
                    if system.lifecycle_stage in {"design", "development", "testing"}
                    else "completed",
                    nist_govern={
                        "accountable_owner": system.owner,
                        "policy": "AI policy and EU AI Act role recorded",
                    },
                    nist_map={
                        "context": system.business_purpose,
                        "affected_parties": ["customers", "operators"],
                    },
                    nist_measure={
                        "metrics": ["accuracy", "drift", "privacy boundary", "human override"],
                    },
                    nist_manage={
                        "controls": ["human review", "logging", "incident escalation"],
                    },
                    data_provenance="Sources, licenses, lineage, and transformations must be documented before approval.",
                    data_quality="Quality review covers representativeness, bias, completeness, and fitness for intended use.",
                    training_data_protections="Training data is encrypted, access-controlled, minimized, and excluded from provider foundation-model training.",
                    residual_risk="high" if system.medical_device_related else "medium",
                    approval_status="pending review",
                )
            )
            created["impact_assessments"] += 1

        review = db.scalar(
            select(AIGovernanceReview).where(
                AIGovernanceReview.ai_system_id == system.id,
                AIGovernanceReview.review_type == "deployment readiness",
            )
        )
        if review is None:
            if system.medical_device_related:
                status = "under review"
                risk_level = "high"
                next_review = date.today() + timedelta(days=14)
                decision = "Clinical validation, SOUP supplier evidence, and human oversight records are required before production approval."
            elif system.lifecycle_stage == "deployed":
                status = "approved with conditions"
                risk_level = "medium"
                next_review = date.today() - timedelta(days=10)
                decision = "Approved for private endpoint use with quarterly evidence refresh and provider documentation review."
            else:
                status = "pending evidence"
                risk_level = "medium"
                next_review = date.today() + timedelta(days=30)
                decision = "Transparency notice and evaluation record must be accepted before general availability."

            review = AIGovernanceReview(
                ai_system_id=system.id,
                review_name=f"{system.name} deployment readiness",
                review_type="deployment readiness",
                status=status,
                risk_level=risk_level,
                reviewer="AI Governance Council",
                decision_summary=decision,
                next_review_date=next_review,
            )
            db.add(review)
            db.flush()
            created["governance_reviews"] += 1

        evidence_templates = [
            (
                "Risk assessment",
                "assessment",
                f"{system.name} impact and risk assessment",
                "accepted",
                "Control owner reviewed residual risk and mitigation plan.",
            ),
            (
                "Data governance",
                "attestation",
                f"{system.name} data provenance and training exclusion",
                "provided" if not system.medical_device_related else "missing",
                "Data source, retention, and training boundary evidence.",
            ),
            (
                "Human oversight",
                "procedure",
                f"{system.name} human oversight procedure",
                "provided" if system.lifecycle_stage == "deployed" else "missing",
                "Reviewer roles, override path, and escalation workflow.",
            ),
            (
                "Transparency notice",
                "notice",
                f"{system.name} user and customer notice",
                "accepted" if system.lifecycle_stage == "deployed" else "missing",
                "EU AI Act notice and customer-facing disclosure package.",
            ),
        ]
        for requirement, evidence_type, title, status, notes in evidence_templates:
            exists = db.scalar(
                select(AIEvidenceItem).where(
                    AIEvidenceItem.review_id == review.id,
                    AIEvidenceItem.requirement == requirement,
                )
            )
            if exists is None:
                db.add(
                    AIEvidenceItem(
                        review_id=review.id,
                        requirement=requirement,
                        evidence_type=evidence_type,
                        title=title,
                        evidence_uri=""
                        if status == "missing"
                        else f"trust://ai-evidence/{system.name.lower().replace(' ', '-')}/{requirement.lower().replace(' ', '-')}",
                        owner=system.owner,
                        status=status,
                        notes=notes,
                    )
                )
                created["evidence_items"] += 1

        if system.medical_device_related and not db.scalar(
            select(MedicalAIAlgorithmicRiskAssessment).where(
                MedicalAIAlgorithmicRiskAssessment.ai_system_id == system.id
            )
        ):
            db.add(
                MedicalAIAlgorithmicRiskAssessment(
                    ai_system_id=system.id,
                    soup_component_id=soup_component.id,
                    training_validation_test_split_risk=(
                        "Engineers must document training, validation, and test split strategy, "
                        "leakage prevention, stratification, "
                        "clinical representativeness, and locked test-set governance."
                    ),
                    explainable_ai_evaluation=(
                        "Assessment must explain whether outputs are causally meaningful or only "
                        "correlational, and how clinicians should interpret uncertainty."
                    ),
                    performative_prediction_risk=(
                        "Review must address whether the prediction changes clinical behavior in a "
                        "way that changes the predicted outcome and creates feedback loops."
                    ),
                    clinical_validation_status="protocol required",
                    risk_controls="Clinician override, locked validation protocol, post-market monitoring, and SOUP supplier review.",
                    review_status="required",
                )
            )
            created["medical_risks"] += 1

    for framework, status, coverage, monitored, summary in TRUST_CENTER_FRAMEWORKS:
        exists = db.scalar(
            select(TrustCenterFrameworkStatus).where(
                TrustCenterFrameworkStatus.framework == framework
            )
        )
        if exists is None:
            db.add(
                TrustCenterFrameworkStatus(
                    framework=framework,
                    status=status,
                    coverage_percent=coverage,
                    monitored_controls=monitored,
                    public_summary=summary,
                )
            )
            created["trust_center"] += 1

    systems = list(db.scalars(select(AISystemInventory)))
    for system in systems:
        if not db.scalar(
            select(TrustCenterAITransparencyMetric).where(
                TrustCenterAITransparencyMetric.system_name == system.name
            )
        ):
            latest = db.scalar(
                select(AIRiskClassification)
                .where(AIRiskClassification.ai_system_id == system.id)
                .order_by(AIRiskClassification.created_at.desc())
            )
            answers = latest.questionnaire_answers if latest else {}
            notice_required = any(
                bool(answers.get(k))
                for k in [
                    "direct_user_interaction",
                    "biometric_categorization_or_emotion",
                    "synthetic_content_or_deepfake",
                ]
            )
            db.add(
                TrustCenterAITransparencyMetric(
                    ai_system_id=system.id,
                    system_name=system.name,
                    direct_user_interaction=bool(answers.get("direct_user_interaction")),
                    biometric_data=bool(answers.get("biometric_categorization_or_emotion")),
                    synthetic_content=bool(answers.get("synthetic_content_or_deepfake")),
                    deepfake_generation=False,
                    eu_transparency_notice="required" if notice_required else "not_required",
                    public_summary=system.business_purpose,
                )
            )
            created["trust_center"] += 1

    for doc_name in [
        "SOC 2 Type 2 Report",
        "Penetration Test Executive Summary",
        "HIPAA Safeguards Summary",
        "AI System Transparency Package",
    ]:
        exists = db.scalar(
            select(TrustCenterDocumentRequest).where(
                TrustCenterDocumentRequest.document_name == doc_name
            )
        )
        if exists is None:
            db.add(
                TrustCenterDocumentRequest(
                    document_name=doc_name,
                    request_workflow=(
                        "Requester submits business justification, automated NDA is executed, "
                        "then document access is approved and watermarked."
                    ),
                )
            )
            created["trust_center"] += 1

    db.commit()
    return created


def seed_ai_governance(db: Session) -> dict[str, int]:
    """Seed AI governance reference + demo data (used by tests and demo runs)."""
    created = seed_ai_reference(db)
    created.update(seed_ai_demo(db))
    return created
