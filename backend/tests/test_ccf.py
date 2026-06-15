"""Tests for the CCF core — Iteration 1."""

from __future__ import annotations

from app.seed.ccf_reference import COMMON_CONTROLS, FRAMEWORKS


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_reports_frameworks(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["frameworks"] == len(FRAMEWORKS)


def test_summary_counts(client):
    data = client.get("/api/summary").json()
    assert data["frameworks"] == len(FRAMEWORKS)
    assert data["common_controls"] == len(COMMON_CONTROLS)
    # Every common control maps to >= 1 requirement, so mappings exceed controls.
    assert data["mappings"] >= data["common_controls"]
    assert data["requirements"] > 0


def test_list_frameworks(client):
    frameworks = client.get("/api/frameworks").json()
    keys = {f["key"] for f in frameworks}
    assert {"soc2", "pci_dss", "nist_800_53"} <= keys
    for fw in frameworks:
        assert fw["requirement_count"] > 0
        assert fw["category"] == "enterprise"


def test_filter_frameworks_by_category(client):
    medical = client.get("/api/frameworks", params={"category": "medical"}).json()
    assert medical == []  # medical subsystem arrives in a later iteration


def test_coverage_proves_many_to_many(client):
    """The core payoff: a single control satisfies multiple frameworks."""
    coverage = client.get("/api/coverage").json()
    assert len(coverage) == len(COMMON_CONTROLS)

    crypto = next(c for c in coverage if c["key"] == "CCF-CRYPTO-001")
    # Data Encryption at Rest must light up SOC 2, PCI DSS, and NIST 800-53.
    assert set(crypto["frameworks_covered"]) == {"SOC 2", "PCI DSS", "NIST 800-53"}
    assert len(crypto["requirements"]) == 3

    citations = {(r["framework_key"], r["citation"]) for r in crypto["requirements"]}
    assert ("nist_800_53", "SC-28") in citations
    assert ("pci_dss", "3.5") in citations


def test_requirements_endpoint(client):
    frameworks = client.get("/api/frameworks").json()
    soc2 = next(f for f in frameworks if f["key"] == "soc2")
    reqs = client.get(f"/api/frameworks/{soc2['id']}/requirements").json()
    assert any(r["citation"] == "CC6.1" for r in reqs)


def test_seed_is_idempotent(db_session):
    """Re-running the seeder must not duplicate rows."""
    with db_session() as session:
        created = seed_again(session)
    assert created == {
        "frameworks": 0,
        "requirements": 0,
        "controls": 0,
        "mappings": 0,
    }


def seed_again(session):
    from app.seed.seeder import seed_ccf

    return seed_ccf(session)
