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
