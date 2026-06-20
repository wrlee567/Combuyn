"""Tests for the AI Governance module."""

from __future__ import annotations


def test_iso42001_annex_a_control_catalog(client):
    controls = client.get("/api/ai-governance/iso42001/controls").json()
    assert len(controls) == 38

    objective_codes = {c["objective_code"] for c in controls}
    assert objective_codes == {
        "A.2",
        "A.3",
        "A.4",
        "A.5",
        "A.6",
        "A.7",
        "A.8",
        "A.9",
        "A.10",
    }
    assert any(c["control_id"] == "A.6.4" for c in controls)
    assert any(c["control_id"] == "A.7.4" for c in controls)


def test_ai_governance_summary_counts(client):
    summary = client.get("/api/ai-governance/summary").json()
    assert summary["ai_systems"] == 3
    assert summary["iso42001_controls"] == 38
    assert summary["high_risk_systems"] == 1
    assert summary["gpai_systems"] == 1
    assert summary["open_tasks"] >= 1
    assert summary["evidence_items"] == 12
    assert summary["missing_evidence"] >= 1
    assert summary["overdue_reviews"] == 1


def test_seeded_systems_have_expected_classification_tiers(client):
    systems = client.get("/api/ai-governance/systems").json()
    tiers = {s["name"]: s["latest_classification"]["risk_tier"] for s in systems}

    assert tiers["Medical Triage Risk Scorer"] == "High-Risk Systems"
    assert tiers["Foundation Model Gateway"] == "General Purpose AI (GPAI) Models"
    assert tiers["Vendor Risk Copilot"] == "Limited Risk Systems"


def test_classification_endpoint_generates_role_specific_tasks(client):
    system = client.get("/api/ai-governance/systems").json()[0]
    response = client.post(
        "/api/ai-governance/classifications",
        json={
            "ai_system_id": system["id"],
            "actor_role": "Provider",
            "questionnaire_answers": {
                "ai_system": True,
                "placed_on_eu_market": True,
                "medical_or_critical_infrastructure": True,
                "safety_component_or_regulated_product": True,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["risk_tier"] == "High-Risk Systems"

    tasks = client.get("/api/ai-governance/tasks").json()
    provider_tasks = [
        t for t in tasks if t["owner_role"] == "Provider" and t["ai_system_id"] == system["id"]
    ]
    assert any("risk management system" in t["obligation"] for t in provider_tasks)
    assert any("technical documentation" in t["obligation"] for t in provider_tasks)


def test_guardrails_and_medical_risk_are_exposed(client):
    guardrails = client.get("/api/ai-governance/guardrails").json()
    assert len(guardrails) == 3
    assert all(g["customer_data_training_blocked"] for g in guardrails)
    assert all(g["encryption_at_rest"] for g in guardrails)

    medical = client.get("/api/ai-governance/medical-risk").json()
    assert len(medical) == 1
    assert "training" in medical[0]["training_validation_test_split_risk"].lower()
    assert "causally" in medical[0]["explainable_ai_evaluation"].lower()
    assert "feedback loops" in medical[0]["performative_prediction_risk"].lower()


def test_governance_reviews_expose_evidence_register(client):
    reviews = client.get("/api/ai-governance/reviews").json()
    assert len(reviews) == 3
    assert all(len(review["evidence_items"]) == 4 for review in reviews)
    assert any(review["status"] == "approved with conditions" for review in reviews)
    assert any(review["evidence_missing"] > 0 for review in reviews)

    medical = next(
        review
        for review in reviews
        if review["system_name"] == "Medical Triage Risk Scorer"
    )
    assert medical["risk_level"] == "high"
    assert any(
        item["requirement"] == "Data governance" and item["status"] == "missing"
        for item in medical["evidence_items"]
    )


def test_public_trust_center(client):
    trust = client.get("/api/trust-center").json()
    frameworks = {f["framework"] for f in trust["frameworks"]}

    assert {"SOC 2", "ISO 27001", "HIPAA", "EU AI Act", "ISO/IEC 42001"} <= frameworks
    assert len(trust["documents"]) >= 3
    assert any(t["eu_transparency_notice"] == "required" for t in trust["ai_transparency"])
