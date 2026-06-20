"""Tests for database.py — URL normalization and session lifecycle."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.database import _normalize_url, get_db


def test_normalize_postgres_scheme():
    assert _normalize_url("postgres://user:pw@host/db") == "postgresql+psycopg://user:pw@host/db"


def test_normalize_postgresql_scheme():
    assert _normalize_url("postgresql://user:pw@host/db") == "postgresql+psycopg://user:pw@host/db"


def test_normalize_already_correct_url():
    url = "postgresql+psycopg://user:pw@host/db"
    assert _normalize_url(url) == url


def test_normalize_sqlite_passthrough():
    url = "sqlite:///:memory:"
    assert _normalize_url(url) == url


def test_get_db_yields_and_closes():
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    try:
        next(gen)
    except StopIteration:
        pass


def test_create_schema_on_startup_defaults_off_in_production():
    from app.config import Settings

    prod = Settings(environment="production", database_url="sqlite://")
    assert prod.create_schema_on_startup is False

    dev = Settings(environment="development", database_url="sqlite://")
    assert dev.create_schema_on_startup is True

    # Explicit override wins over the environment default.
    forced = Settings(
        environment="production", auto_create_schema=True, database_url="sqlite://"
    )
    assert forced.create_schema_on_startup is True
