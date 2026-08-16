"""
Health check and readiness API routes.
"""

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
            },
        )

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENV.value,
        "database": db_status,
        "debug": settings.DEBUG,
    }
