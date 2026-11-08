"""
Health check and readiness API routes.
"""

import os
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check verifying application and database status.
    """
    db_status = "connected"
    db_type = "postgresql" if not str(db.bind.url).startswith("sqlite") else "sqlite"
    try:
        # Perform live database ping
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "app": settings.APP_NAME,
                "environment": settings.ENV.value,
                "database": db_status,
                "database_type": db_type,
            },
        )

    # In production, verify that a persistent database is in use
    is_prod = settings.is_production or (
        (os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None)
        and (settings.ENV.value == "production" or os.environ.get("VERCEL_ENV") == "production")
    )
    if is_prod and db_type == "sqlite":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "app": settings.APP_NAME,
                "environment": settings.ENV.value,
                "database": "unhealthy: production requires hosted PostgreSQL (ephemeral SQLite detected)",
                "database_type": "sqlite",
            },
        )

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENV.value,
        "database": db_status,
        "database_type": db_type,
        "debug": settings.DEBUG,
    }
