"""AI governance workflow logic.

The service layer keeps regulatory decision logic out of the API router and
seed data. It intentionally returns transparent rationales so reviewers can
see why a system landed in an EU AI Act tier.
"""

from __future__ import annotations

from dataclasses import dataclass


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
