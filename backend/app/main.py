"""Combuyn FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import ai_governance, ccf, health
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.seed.ai_governance import seed_ai_governance
from app.seed.seeder import seed_ccf

# Ensure models are registered on Base.metadata.
import app.models  # noqa: F401  (side-effect import)

logger = logging.getLogger("combuyn")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iteration 1 uses create_all for a frictionless first run; Alembic
    # migrations (committed under alembic/) become the source of truth as the
    # schema evolves in later iterations.
    Base.metadata.create_all(bind=engine)

    if settings.seed_on_startup:
        with SessionLocal() as db:
            created = seed_ccf(db)
            ai_created = seed_ai_governance(db)
        if any(created.values()):
            logger.info("Seeded CCF reference data: %s", created)
        if any(ai_created.values()):
            logger.info("Seeded AI governance reference data: %s", ai_created)
    yield


app = FastAPI(
    title="Combuyn API",
    description="Automated GRC platform — Common Control Framework core.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ccf.router)
app.include_router(ai_governance.router)
app.include_router(ai_governance.trust_router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"name": "Combuyn", "tagline": "buy in to compliance", "docs": "/docs"}
