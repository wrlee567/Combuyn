"""Database engine, session factory, and the declarative base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def _normalize_url(url: str) -> str:
    """Normalize provider-supplied URLs to the psycopg3 driver.

    Render (and Heroku-style providers) hand out URLs beginning with
    ``postgres://`` or ``postgresql://``. SQLAlchemy 2.x needs an explicit
    driver, so we upgrade those to ``postgresql+psycopg://``. SQLite URLs
    (used in tests) are passed through untouched.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


settings = get_settings()
DATABASE_URL = _normalize_url(settings.database_url)

# check_same_thread is only meaningful for SQLite (test runs).
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
