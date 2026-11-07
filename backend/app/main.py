"""
Annotation Quality Guardian — FastAPI Main Application Entry Point
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_backend_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
_scoring_dir = os.path.join(_backend_dir, "scoring")
if os.path.exists(_scoring_dir) and _scoring_dir not in sys.path:
    sys.path.insert(0, _scoring_dir)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import engine, Base, check_db_connection

import app.models  # Ensure all SQLAlchemy models are registered

from app.api import (
    health,
    annotations,
    projects,
    scores,
    review,
    export,
    ingestion,
    jobs,
    webhook,
    dashboard,
    project_settings,
    integrations,
    rerouting,
    ab_testing,
    ambiguity,
    auth,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    Ensures required tables, schema compatibility, and demo accounts exist.
    """
    try:
        if check_db_connection():
            Base.metadata.create_all(bind=engine)
            from app.core.db_patch import ensure_schema_compatibility
            ensure_schema_compatibility(engine)
            if not settings.is_testing:
                from app.core.seed_demo_data import seed_demo_data, seed_demo_users
                from app.core.db import SessionLocal
                from app.models.user import User
                from app.models.project import Project

                with SessionLocal() as db:
                    user_count = db.query(User).count()
                    if user_count == 0:
                        seed_demo_users(db)

                    project_count = db.query(Project).count()
                    if project_count == 0:
                        seed_demo_data()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Startup DB initialization notice: %s", exc)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Quality assurance platform scoring data annotations "
        "via multi-signal trust metrics."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ── CORS Middleware ────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Include Routers ────────────────────────────────────────────────

app.include_router(health.router)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    annotations.router,
    prefix="/api/annotations",
    tags=["Annotations"],
)

app.include_router(
    projects.router,
    prefix="/api",
    tags=["Projects"],
),


app.include_router(
    scores.router,
    prefix="/api/scores",
    tags=["Scores"],
)

app.include_router(
    review.router,
    prefix="/api/review",
    tags=["Review Queue"],
)

app.include_router(ingestion.router)

app.include_router(
    ingestion.router,
    prefix="/api",
    tags=["Ingestion"],
)

app.include_router(export.router, prefix="/api/projects", tags=["Export"])


app.include_router(
    jobs.router,
    prefix="/api",
)

app.include_router(
    webhook.router,
    prefix="/api",
    tags=["Webhook Ingestion"],
)

app.include_router(
    dashboard.router,
    prefix="/api",
    tags=["Dashboard"],
)

app.include_router(
    project_settings.router,
    prefix="/api",
    tags=["Project Settings"],
)

app.include_router(
    integrations.router,
    prefix="/api",
    tags=["Integrations & DB Connectors"],
)

app.include_router(
    rerouting.router,
    prefix="/api",
    tags=["Task Rerouting"],
)

app.include_router(
    rerouting.automation_router,
    prefix="/api",
    tags=["Automation Dashboard"],
)

app.include_router(
    ab_testing.router,
    prefix="/api",
    tags=["A/B Testing"],
)

app.include_router(
    ambiguity.router,
    prefix="/api",
    tags=["Ambiguity Insights"],
)


# ── Root Endpoint ─────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Root metadata endpoint."""
    return {
        "service": settings.APP_NAME,
        "environment": settings.ENV.value,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
    }