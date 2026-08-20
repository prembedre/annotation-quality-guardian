"""
Annotation Quality Guardian — FastAPI Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import engine, Base, check_db_connection
import app.models  # Ensure all SQLAlchemy models are registered
from app.api import health, annotations, projects, scores, review, export, ingestion, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    In development, ensure base tables exist if not yet migrated.
    """
    if settings.is_development and check_db_connection():
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Quality assurance platform scoring data annotations via multi-signal trust metrics.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(annotations.router, prefix="/api/annotations", tags=["Annotations"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(scores.router, prefix="/api/scores", tags=["Scores"])
app.include_router(review.router, prefix="/api/review", tags=["Review Queue"])
app.include_router(ingestion.router)
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(jobs.router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root metadata endpoint."""
    return {
        "service": settings.APP_NAME,
        "environment": settings.ENV.value,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
    }
