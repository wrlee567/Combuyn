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

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed.seeder import seed_ccf, seed_vendors, seed_workflows  # noqa: E402


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
        seed_workflows(session)

    yield TestingSession
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
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
