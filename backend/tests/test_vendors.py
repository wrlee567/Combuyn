"""Tests for the TPRM Vendor API — Iteration 2."""

from __future__ import annotations


def _create(client, **overrides):
    payload = {
        "name": "Acme Corp",
        "industry": "technology",
        "data_classification": "confidential",
        "network_connectivity": "integrated",
        "geography": "domestic",
    }
    payload.update(overrides)
    return client.post("/api/vendors", json=payload)


def test_sample_vendors_seeded(client):
    vendors = client.get("/api/vendors").json()
    names = {v["name"] for v in vendors}
    assert "Northwind Payments" in names
    # Listing is ordered by descending risk — the payments vendor should top it.
    assert vendors[0]["inherent_risk_score"] >= vendors[-1]["inherent_risk_score"]


def test_create_vendor_computes_risk(client):
    resp = _create(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["inherent_risk_score"] > 0
    assert body["inherent_risk_tier"] in {"Low", "Medium", "High", "Critical"}
    assert set(body["risk_breakdown"]) == {
        "data_classification",
        "network_connectivity",
        "industry",
        "geography",
    }


def test_low_vs_high_risk_ordering(client):
    low = _create(
        client,
        name="Low Risk Vendor",
        data_classification="public",
        network_connectivity="none",
        industry="retail",
        geography="domestic",
    ).json()
    high = _create(
        client,
        name="High Risk Vendor",
        data_classification="restricted",
        network_connectivity="privileged",
        industry="healthcare",
        geography="high_risk",
    ).json()
    assert high["inherent_risk_score"] > low["inherent_risk_score"]


def test_create_invalid_factor_returns_422(client):
    resp = _create(client, data_classification="bogus")
    assert resp.status_code == 422


def test_create_invalid_lifecycle_returns_422(client):
    resp = _create(client, lifecycle_status="bogus")
    assert resp.status_code == 422


def test_get_vendor_and_404(client):
    created = _create(client).json()
    got = client.get(f"/api/vendors/{created['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "Acme Corp"

    missing = client.get("/api/vendors/00000000-0000-0000-0000-000000000099")
    assert missing.status_code == 404


def test_questionnaire_update_merges(client):
    vendor = _create(client).json()
    vid = vendor["id"]

    r1 = client.patch(
        f"/api/vendors/{vid}/questionnaire",
        json={"responses": {"mfa_enforced": True}},
    )
    assert r1.status_code == 200

    r2 = client.patch(
        f"/api/vendors/{vid}/questionnaire",
        json={"responses": {"encryption_at_rest": True}},
    )
    body = r2.json()
    # Both answers persist (merge, not overwrite).
    assert body["questionnaire_responses"]["mfa_enforced"] is True
    assert body["questionnaire_responses"]["encryption_at_rest"] is True


def test_questionnaire_rejects_unknown_question(client):
    vendor = _create(client).json()
    resp = client.patch(
        f"/api/vendors/{vendor['id']}/questionnaire",
        json={"responses": {"not_a_real_question": True}},
    )
    assert resp.status_code == 422


def test_lifecycle_transition(client):
    vendor = _create(client, lifecycle_status="sourcing").json()
    resp = client.patch(
        f"/api/vendors/{vendor['id']}/lifecycle",
        json={"lifecycle_status": "offboarding"},
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_status"] == "offboarding"


def test_options_and_template(client):
    options = client.get("/api/vendors/options").json()
    assert "financial_services" in options["factors"]["industry"]
    assert "offboarding" in options["lifecycle_phases"]

    template = client.get("/api/vendors/questionnaire-template").json()
    assert template["version"]
    assert any(s["section"] == "Access Control" for s in template["sections"])


def test_get_vendor_invalid_uuid(client):
    resp = client.get("/api/vendors/not-a-uuid")
    assert resp.status_code == 422


def test_create_vendor_missing_required_field(client):
    resp = client.post("/api/vendors", json={"industry": "technology"})
    assert resp.status_code == 422


def test_create_vendor_name_over_limit(client):
    resp = _create(client, name="x" * 256)
    assert resp.status_code == 422


def test_lifecycle_invalid_transition(client):
    vendor = _create(client).json()
    resp = client.patch(
        f"/api/vendors/{vendor['id']}/lifecycle",
        json={"lifecycle_status": "limbo"},
    )
    assert resp.status_code == 422


def test_questionnaire_boolean_answer_accepted(client):
    vendor = _create(client).json()
    resp = client.patch(
        f"/api/vendors/{vendor['id']}/questionnaire",
        json={"responses": {"mfa_enforced": True}},
    )
    assert resp.status_code == 200
    assert resp.json()["questionnaire_responses"]["mfa_enforced"] is True


def test_update_nonexistent_vendor(client):
    resp = client.patch(
        "/api/vendors/00000000-0000-0000-0000-000000000099/lifecycle",
        json={"lifecycle_status": "offboarding"},
    )
    assert resp.status_code == 404
