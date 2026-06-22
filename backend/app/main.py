"""Combuyn FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import ai_governance, auth, ccf, health, vendors, workflow
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.seed.ai_governance import seed_ai_demo, seed_ai_reference
from app.seed.seeder import (
    seed_ccf,
    seed_vendors,
    seed_workflow_definitions,
    seed_workflow_instances,
)

# Ensure models are registered on Base.metadata.
import app.models  # noqa: F401  (side-effect import)

logger = logging.getLogger("combuyn")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_all gives a frictionless first run in local/test. Production
    # (ENVIRONMENT=production, or AUTO_CREATE_SCHEMA=false) instead relies on
    # Alembic migrations run before startup — see backend/README.md.
    if settings.create_schema_on_startup:
        Base.metadata.create_all(bind=engine)

    if settings.seed_on_startup:
        with SessionLocal() as db:
            created = seed_ccf(db)
            ai_ref = seed_ai_reference(db)
            workflow_defs = seed_workflow_definitions(db)
        if any(created.values()):
            logger.info("Seeded CCF reference data: %s", created)
        if any(ai_ref.values()):
            logger.info("Seeded AI governance reference data: %s", ai_ref)
        if workflow_defs:
            logger.info("Seeded workflow definitions: %d", workflow_defs)

    if settings.seed_demo_data:
        with SessionLocal() as db:
            vendors_created = seed_vendors(db)
            ai_demo = seed_ai_demo(db)
            workflow_instances = seed_workflow_instances(db)
        if vendors_created:
            logger.info("Seeded sample vendors: %d", vendors_created)
        if any(ai_demo.values()):
            logger.info("Seeded AI governance demo data: %s", ai_demo)
        if workflow_instances:
            logger.info("Seeded workflow instances: %d", workflow_instances)
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
app.include_router(auth.router)
app.include_router(ccf.router)
app.include_router(vendors.router)
app.include_router(workflow.router)
app.include_router(ai_governance.router)
app.include_router(ai_governance.trust_router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"name": "Combuyn", "tagline": "buy in to compliance", "docs": "/docs"}
