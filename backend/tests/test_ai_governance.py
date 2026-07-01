"""Tests for the AI Governance module."""

from __future__ import annotations

from app.models.ccf import DEFAULT_ORG_ID
from app.services.ai_governance import (
    build_ai_inventory_summary,
    build_implementation_packets,
    build_launch_gate_payload,
    build_public_trust_center,
    list_ai_governance_reviews,
    list_ai_systems,
)


def test_ai_governance_service_assembles_dashboard_summary(db_session):
    with db_session() as db:
        summary = build_ai_inventory_summary(db, DEFAULT_ORG_ID)

    assert summary.ai_systems == 3
    assert summary.iso42001_controls == 38
    assert summary.high_risk_systems == 1
    assert summary.gpai_systems == 1
    assert summary.evidence_items == 13
    assert summary.overdue_reviews == 1


def test_ai_governance_service_attaches_latest_classification(db_session):
    with db_session() as db:
        systems = list_ai_systems(db, DEFAULT_ORG_ID)

    tiers = {system.name: system.latest_classification.risk_tier for system in systems}
    assert tiers["Medical Triage Risk Scorer"] == "High-Risk Systems"
    assert tiers["Foundation Model Gateway"] == "General Purpose AI (GPAI) Models"
    assert tiers["Vendor Risk Copilot"] == "Limited Risk Systems"


def test_ai_governance_service_counts_review_evidence(db_session):
    with db_session() as db:
        reviews = list_ai_governance_reviews(db, DEFAULT_ORG_ID)

    medical = next(
        review
        for review in reviews
        if review.system_name == "Medical Triage Risk Scorer"
    )
    assert medical.evidence_ready == 1
    assert medical.evidence_missing == 4
    assert [item.requirement for item in medical.evidence_items] == sorted(
        item.requirement for item in medical.evidence_items
    )


def test_ai_governance_service_builds_public_trust_center(db_session):
    with db_session() as db:
        trust = build_public_trust_center(db)

    frameworks = {framework.framework for framework in trust.frameworks}
    assert {"SOC 2", "ISO 27001", "HIPAA", "EU AI Act", "ISO/IEC 42001"} <= frameworks
    assert len(trust.documents) >= 3
    assert any(
        metric.eu_transparency_notice == "required"
        for metric in trust.ai_transparency
    )


def test_launch_gate_payload_includes_required_artifacts(db_session):
    with db_session() as db:
        systems = list_ai_systems(db, DEFAULT_ORG_ID)
        system = next(s for s in systems if s.name == "Vendor Risk Copilot")
        gate = build_launch_gate_payload(db, DEFAULT_ORG_ID, system.id)

    assert gate is not None
    assert gate.system.name == "Vendor Risk Copilot"
    assert gate.latest_classification is not None
    assert gate.tasks
    assert gate.guardrails is not None
    assert gate.impact_assessment is not None
    assert gate.governance_review is not None
    assert len(gate.evidence_items) == 4
    assert gate.trust_center_transparency is not None
    assert gate.readiness.state == "ready"


def test_missing_evidence_blocks_launch_approval_service(db_session):
    with db_session() as db:
        systems = list_ai_systems(db, DEFAULT_ORG_ID)
        system = next(s for s in systems if s.name == "Medical Triage Risk Scorer")
        gate = build_launch_gate_payload(db, DEFAULT_ORG_ID, system.id)

    assert gate is not None
    assert gate.readiness.state == "blocked"
    assert gate.readiness.evidence_missing == 4
    assert gate.readiness.approval_blockers


def test_evidence_updates_change_launch_gate_readiness_counts(client):
    system = next(
        s for s in client.get("/api/ai-governance/systems").json()
        if s["name"] == "Medical Triage Risk Scorer"
    )
    gate = client.get(f"/api/ai-governance/systems/{system['id']}/launch-gate").json()
    missing = next(item for item in gate["evidence_items"] if item["status"] == "missing")

    response = client.patch(
        f"/api/ai-governance/evidence/{missing['id']}",
        json={
            "status": "provided",
            "evidence_uri": "trust://ai-evidence/medical-triage-risk-scorer/data-governance",
            "notes": "Uploaded for council review.",
        },
    )

    assert response.status_code == 200
    updated_gate = client.get(
        f"/api/ai-governance/systems/{system['id']}/launch-gate"
    ).json()
    assert updated_gate["readiness"]["evidence_ready"] == 1
    assert updated_gate["readiness"]["evidence_missing"] == 3
    assert any(
        "accepted or waived" in blocker
        for blocker in updated_gate["readiness"]["approval_blockers"]
    )


def test_trust_center_sync_reflects_transparency_classification_answers(db_session):
    with db_session() as db:
        systems = list_ai_systems(db, DEFAULT_ORG_ID)
        system = next(s for s in systems if s.name == "Vendor Risk Copilot")
        gate = build_launch_gate_payload(db, DEFAULT_ORG_ID, system.id)

    assert gate is not None
    assert gate.trust_center_transparency is not None
    assert gate.trust_center_transparency.direct_user_interaction is True
    assert gate.trust_center_transparency.eu_transparency_notice == "required"


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
    assert summary["evidence_items"] == 13
    assert summary["missing_evidence"] >= 1
    assert summary["overdue_reviews"] == 1


def test_seeded_systems_have_expected_classification_tiers(client):
    systems = client.get("/api/ai-governance/systems").json()
    tiers = {s["name"]: s["latest_classification"]["risk_tier"] for s in systems}

    assert tiers["Medical Triage Risk Scorer"] == "High-Risk Systems"
    assert tiers["Foundation Model Gateway"] == "General Purpose AI (GPAI) Models"
    assert tiers["Vendor Risk Copilot"] == "Limited Risk Systems"


def test_launch_gate_detail_is_tenant_scoped(db_session, other_org_client):
    with db_session() as db:
        system = list_ai_systems(db, DEFAULT_ORG_ID)[0]

    response = other_org_client.get(
        f"/api/ai-governance/systems/{system.id}/launch-gate"
    )

    assert response.status_code == 404


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
    assert all(len(review["evidence_items"]) >= 4 for review in reviews)
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
    assert any(
        item["requirement"] == "Medical AI validation" and item["status"] == "missing"
        for item in medical["evidence_items"]
    )


def test_implementation_packets_are_generated_for_missing_review_evidence(db_session):
    with db_session() as db:
        reviews = list_ai_governance_reviews(db, DEFAULT_ORG_ID)
        medical = next(
            review
            for review in reviews
            if review.system_name == "Medical Triage Risk Scorer"
        )
        packets = build_implementation_packets(db, DEFAULT_ORG_ID, medical.id)

    assert packets is not None
    assert {packet.requirement_name for packet in packets} == {
        "Data governance",
        "Human oversight",
        "Medical AI validation",
        "Transparency notice",
    }
    data_packet = next(packet for packet in packets if packet.requirement_name == "Data governance")
    assert data_packet.status == "missing"
    assert data_packet.owner == "Medical Device Engineering"
    assert data_packet.implementation_steps
    assert data_packet.evidence_requirements
    assert data_packet.acceptance_criteria


def test_implementation_packet_status_reflects_evidence_status(client):
    review = next(
        r for r in client.get("/api/ai-governance/reviews").json()
        if r["system_name"] == "Medical Triage Risk Scorer"
    )
    evidence = next(
        item for item in review["evidence_items"] if item["requirement"] == "Data governance"
    )

    response = client.patch(
        f"/api/ai-governance/evidence/{evidence['id']}",
        json={
            "status": "provided",
            "evidence_uri": "trust://ai-evidence/medical/data-governance",
        },
    )
    assert response.status_code == 200

    packets = client.get(
        f"/api/ai-governance/reviews/{review['id']}/implementation-packets"
    ).json()
    packet = next(packet for packet in packets if packet["requirement_name"] == "Data governance")
    assert packet["status"] == "provided"
    assert packet["evidence_uri"] == "trust://ai-evidence/medical/data-governance"


def test_rejected_evidence_blocks_approval(client):
    review = next(
        r for r in client.get("/api/ai-governance/reviews").json()
        if r["system_name"] == "Vendor Risk Copilot"
    )
    evidence = review["evidence_items"][0]
    assert client.patch(
        f"/api/ai-governance/evidence/{evidence['id']}",
        json={"status": "rejected"},
    ).status_code == 200

    response = client.patch(
        f"/api/ai-governance/reviews/{review['id']}/decision",
        json={
            "status": "approved",
            "decision_summary": "Approved for launch.",
            "next_review_date": "2026-09-30",
        },
    )

    assert response.status_code == 409
    assert "Rejected evidence" in response.json()["detail"]


def test_accepted_evidence_clears_implementation_packet(client):
    review = next(
        r for r in client.get("/api/ai-governance/reviews").json()
        if r["system_name"] == "Medical Triage Risk Scorer"
    )
    evidence = next(
        item for item in review["evidence_items"] if item["requirement"] == "Data governance"
    )

    assert client.patch(
        f"/api/ai-governance/evidence/{evidence['id']}",
        json={
            "status": "accepted",
            "evidence_uri": "trust://ai-evidence/medical/data-governance",
        },
    ).status_code == 200

    packets = client.get(
        f"/api/ai-governance/reviews/{review['id']}/implementation-packets"
    ).json()
    assert all(packet["requirement_name"] != "Data governance" for packet in packets)


def test_review_packet_detail_is_tenant_scoped(db_session, other_org_client):
    with db_session() as db:
        review = list_ai_governance_reviews(db, DEFAULT_ORG_ID)[0]

    response = other_org_client.get(
        f"/api/ai-governance/reviews/{review.id}/implementation-packets"
    )

    assert response.status_code == 404


def test_invalid_evidence_status_returns_422(client):
    review = client.get("/api/ai-governance/reviews").json()[0]
    evidence = review["evidence_items"][0]

    response = client.patch(
        f"/api/ai-governance/evidence/{evidence['id']}",
        json={"status": "almost_ready"},
    )

    assert response.status_code == 422


def test_approval_is_rejected_while_evidence_is_missing(client):
    review = next(
        r for r in client.get("/api/ai-governance/reviews").json()
        if r["system_name"] == "Medical Triage Risk Scorer"
    )

    response = client.patch(
        f"/api/ai-governance/reviews/{review['id']}/decision",
        json={
            "status": "approved",
            "decision_summary": "Approved for launch.",
            "next_review_date": "2026-09-30",
        },
    )

    assert response.status_code == 409
    assert "Missing evidence" in response.json()["detail"]


def test_approval_succeeds_once_evidence_is_complete(client):
    system = next(
        s for s in client.get("/api/ai-governance/systems").json()
        if s["name"] == "Medical Triage Risk Scorer"
    )
    gate = client.get(f"/api/ai-governance/systems/{system['id']}/launch-gate").json()

    for item in gate["evidence_items"]:
        if item["status"] == "missing":
            response = client.patch(
                f"/api/ai-governance/evidence/{item['id']}",
                json={
                    "status": "accepted",
                    "evidence_uri": f"trust://ai-evidence/medical/{item['requirement'].lower().replace(' ', '-')}",
                    "notes": "Provided for launch approval.",
                },
            )
            assert response.status_code == 200

    response = client.patch(
        f"/api/ai-governance/reviews/{gate['governance_review']['id']}/decision",
        json={
            "status": "approved",
            "decision_summary": "Approved after evidence package completion.",
            "next_review_date": "2026-09-30",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_public_trust_center(client):
    trust = client.get("/api/trust-center").json()
    frameworks = {f["framework"] for f in trust["frameworks"]}

    assert {"SOC 2", "ISO 27001", "HIPAA", "EU AI Act", "ISO/IEC 42001"} <= frameworks
    assert len(trust["documents"]) >= 3
    assert any(t["eu_transparency_notice"] == "required" for t in trust["ai_transparency"])

def test_classification_rejects_unknown_keys(client):
    system = client.get("/api/ai-governance/systems").json()[0]
    response = client.post(
        "/api/ai-governance/classifications",
        json={
            "ai_system_id": system["id"],
            "actor_role": "Provider",
            "questionnaire_answers": {"ai_system": True, "bogus_key": True},
        },
    )
    assert response.status_code == 422


def test_classification_rejects_non_boolean_answers(client):
    system = client.get("/api/ai-governance/systems").json()[0]
    response = client.post(
        "/api/ai-governance/classifications",
        json={
            "ai_system_id": system["id"],
            "actor_role": "Provider",
            # String "false" must not be accepted as a boolean answer.
            "questionnaire_answers": {"ai_system": True, "placed_on_eu_market": "false"},
        },
    )
    assert response.status_code == 422
