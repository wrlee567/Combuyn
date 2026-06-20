"""Pytest fixtures — an in-memory SQLite app with seeded CCF data.

Tests run against SQLite (no Postgres needed in CI for the unit tier); the
cross-dialect column types in app.models.types make the same models work on
both engines.
"""

from __future__ import annotations

import os

# Point the global app engine at throwaway SQLite and disable startup seeding
# BEFORE importing any app module (app.database builds the engine at import
# time and the lifespan would otherwise try to reach Postgres).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_ON_STARTUP"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import uuid  # noqa: E402

from app.auth import create_access_token  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.ccf import DEFAULT_ORG_ID  # noqa: E402
from app.seed.ai_governance import seed_ai_governance  # noqa: E402
from app.seed.seeder import seed_ccf, seed_vendors  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSession() as session:
        seed_ccf(session)
        seed_vendors(session)
        seed_ai_governance(session)

    yield TestingSession
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def _test_client(db_session):
    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client(_test_client):
    """Authenticated client scoped to the seeded default tenant."""
    token = create_access_token(DEFAULT_ORG_ID)
    _test_client.headers["Authorization"] = f"Bearer {token}"
    return _test_client


@pytest.fixture()
def anon_client(_test_client):
    """Client with no bearer token — used to assert 401 on protected routes."""
    return _test_client


@pytest.fixture()
def other_org_client(_test_client):
    """Authenticated client for a different tenant (no seeded data)."""
    token = create_access_token(uuid.uuid4())
    _test_client.headers["Authorization"] = f"Bearer {token}"
    return _test_client
