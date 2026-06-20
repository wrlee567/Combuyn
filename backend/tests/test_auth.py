"""Authentication and tenant-isolation tests."""

from __future__ import annotations

import pytest

# Protected GET endpoints across every router.
PROTECTED_GETS = [
    "/api/summary",
    "/api/frameworks",
    "/api/controls",
    "/api/coverage",
    "/api/vendors",
    "/api/ai-governance/summary",
    "/api/ai-governance/systems",
    "/api/ai-governance/iso42001/controls",
    "/api/ai-governance/tasks",
    "/api/ai-governance/guardrails",
    "/api/ai-governance/vendors",
]


@pytest.mark.parametrize("path", PROTECTED_GETS)
def test_protected_routes_require_auth(anon_client, path):
    assert anon_client.get(path).status_code == 401


def test_invalid_token_is_rejected(anon_client):
    anon_client.headers["Authorization"] = "Bearer not-a-real-jwt"
    assert anon_client.get("/api/vendors").status_code == 401


def test_health_and_trust_center_stay_public(anon_client):
    assert anon_client.get("/health").status_code == 200
    assert anon_client.get("/ready").status_code == 200
    assert anon_client.get("/api/trust-center").status_code == 200


def test_authenticated_default_tenant_sees_seeded_data(client):
    assert len(client.get("/api/vendors").json()) > 0
    assert len(client.get("/api/frameworks").json()) > 0
    assert len(client.get("/api/ai-governance/systems").json()) > 0


def test_other_tenant_sees_no_data(other_org_client):
    assert other_org_client.get("/api/vendors").json() == []
    assert other_org_client.get("/api/frameworks").json() == []
    assert other_org_client.get("/api/ai-governance/systems").json() == []
    summary = other_org_client.get("/api/summary").json()
    assert summary["frameworks"] == 0


def test_cross_tenant_vendor_access_returns_404(client, _test_client):
    # Create a vendor as the default tenant.
    created = client.post("/api/vendors", json={"name": "Tenant A Vendor"}).json()
    vendor_id = created["id"]
    assert client.get(f"/api/vendors/{vendor_id}").status_code == 200

    # A different tenant must not be able to read it.
    from app.auth import create_access_token
    import uuid

    _test_client.headers["Authorization"] = f"Bearer {create_access_token(uuid.uuid4())}"
    assert _test_client.get(f"/api/vendors/{vendor_id}").status_code == 404
    assert (
        _test_client.patch(
            f"/api/vendors/{vendor_id}/lifecycle",
            json={"lifecycle_status": "onboarding"},
        ).status_code
        == 404
    )
