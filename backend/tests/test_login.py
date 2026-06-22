"""Tests for the /api/auth/login endpoint."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.seed.demo_user import seed_demo_user

settings = get_settings()


@pytest.fixture()
def seeded_client(_test_client, db_session):
    """Client with the demo user seeded into the test DB."""
    with db_session() as db:
        seed_demo_user(db)
    return _test_client


def test_login_success(seeded_client):
    res = seeded_client.post(
        "/api/auth/login",
        json={"email": settings.demo_user_email, "password": settings.demo_user_password},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "org_id" in body


def test_login_wrong_password(seeded_client):
    res = seeded_client.post(
        "/api/auth/login",
        json={"email": settings.demo_user_email, "password": "wrong"},
    )
    assert res.status_code == 401


def test_login_unknown_email(seeded_client):
    res = seeded_client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert res.status_code == 401


def test_login_token_grants_access(seeded_client):
    """Token returned by login should authenticate subsequent requests."""
    res = seeded_client.post(
        "/api/auth/login",
        json={"email": settings.demo_user_email, "password": settings.demo_user_password},
    )
    token = res.json()["access_token"]
    seeded_client.headers["Authorization"] = f"Bearer {token}"
    assert seeded_client.get("/api/frameworks").status_code == 200


def test_login_missing_fields(seeded_client):
    assert seeded_client.post("/api/auth/login", json={}).status_code == 422
