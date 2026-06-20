"""Tests for the Workflow Orchestration API — Iteration 3."""

from __future__ import annotations


def _create_instance(client, **overrides):
    payload = {
        "definition_key": "vendor_onboarding",
        "subject": "Test Vendor onboarding",
        "context": {"vendor": "Test Vendor"},
    }
    payload.update(overrides)
    return client.post("/api/workflows", json=payload)


def test_definitions_seeded(client):
    defs = client.get("/api/workflows/definitions").json()
    keys = {d["key"] for d in defs}
    assert {"vendor_onboarding", "access_request"} <= keys


def test_definition_detail_includes_blueprint(client):
    defs = client.get("/api/workflows/definitions").json()
    did = next(d["id"] for d in defs if d["key"] == "vendor_onboarding")
    detail = client.get(f"/api/workflows/definitions/{did}").json()
    assert detail["blueprint"]["initial"] == "intake"
    assert any(s["id"] == "approved" for s in detail["blueprint"]["states"])


def test_sample_instances_seeded(client):
    instances = client.get("/api/workflows").json()
    subjects = {i["subject"] for i in instances}
    assert "Cedar Analytics onboarding" in subjects
    # Cedar was driven to completion at seed time.
    cedar = next(i for i in instances if i["subject"] == "Cedar Analytics onboarding")
    assert cedar["current_state"] == "approved"
    assert cedar["status"] == "completed"


def test_create_instance_starts_at_initial(client):
    resp = _create_instance(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["current_state"] == "intake"
    assert body["status"] == "running"
    assert {a["action"] for a in body["available_actions"]} == {"submit"}
    # The start event is logged.
    assert body["events"][0]["kind"] == "start"


def test_create_instance_unknown_definition_404(client):
    resp = _create_instance(client, definition_key="does_not_exist")
    assert resp.status_code == 404


def test_advance_records_transition(client):
    iid = _create_instance(client).json()["id"]
    resp = client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_state"] == "security_review"
    assert {a["action"] for a in body["available_actions"]} == {"pass_security", "reject"}


def test_advance_invalid_action_422(client):
    iid = _create_instance(client).json()["id"]
    resp = client.post(f"/api/workflows/{iid}/advance", json={"action": "approve"})
    assert resp.status_code == 422


def test_advance_to_terminal_completes(client):
    iid = _create_instance(client).json()["id"]
    for action in ["submit", "pass_security", "accept_risk", "approve"]:
        body = client.post(
            f"/api/workflows/{iid}/advance", json={"action": action}
        ).json()
    assert body["current_state"] == "approved"
    assert body["status"] == "completed"
    assert body["available_actions"] == []
    assert any(e["kind"] == "complete" for e in body["events"])


def test_cannot_advance_completed_instance(client):
    iid = _create_instance(client).json()["id"]
    client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    client.post(f"/api/workflows/{iid}/advance", json={"action": "reject"})
    resp = client.post(f"/api/workflows/{iid}/advance", json={"action": "pass_security"})
    assert resp.status_code == 422


def test_compensate_rolls_back(client):
    iid = _create_instance(client).json()["id"]
    client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    client.post(f"/api/workflows/{iid}/advance", json={"action": "pass_security"})

    resp = client.post(f"/api/workflows/{iid}/compensate", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "compensated"
    assert body["current_state"] == "intake"  # back to initial
    # Two forward transitions -> two compensation events.
    comps = [e for e in body["events"] if e["kind"] == "compensation"]
    assert len(comps) == 2
    # Compensation runs in reverse: undo pass_security before undo submit.
    assert comps[0]["from_state"] == "risk_assessment"


def test_compensate_completed_instance_422(client):
    iid = _create_instance(client).json()["id"]
    client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    client.post(f"/api/workflows/{iid}/advance", json={"action": "reject"})
    resp = client.post(f"/api/workflows/{iid}/compensate", json={})
    assert resp.status_code == 422


def test_durable_state_matches_event_replay(client):
    """The persisted current_state must equal a replay of the event log."""
    from app.services.workflow_engine import replay_state

    iid = _create_instance(client).json()["id"]
    client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    body = client.post(
        f"/api/workflows/{iid}/advance", json={"action": "pass_security"}
    ).json()

    transitions = [
        (e["from_state"], e["to_state"])
        for e in body["events"]
        if e["kind"] == "transition" and e["action"]
    ]
    assert replay_state(body["blueprint"], transitions) == body["current_state"]


def test_notifications_feed_records_transitions(client):
    iid = _create_instance(client, subject="Notify Co onboarding").json()["id"]
    client.post(f"/api/workflows/{iid}/advance", json={"action": "submit"})
    feed = client.get("/api/workflows/notifications").json()
    assert feed["channel"]
    assert any("Notify Co onboarding" in n["subject"] for n in feed["notifications"])


def test_get_instance_404(client):
    resp = client.get("/api/workflows/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404
