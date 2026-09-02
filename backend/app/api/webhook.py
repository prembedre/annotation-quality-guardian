"""
API routes for Webhook live ingestion.
Receives real-time JSON payloads from external annotation tools.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.webhook import (
    WebhookAnnotationPayload,
    WebhookAnnotationResponse,
)
from app.services.webhook_service import (
    process_webhook_annotation,
    WebhookIngestionError,
    DuplicateAnnotationError,
)

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook Ingestion"],
)


@router.post(
    "/annotations",
    response_model=WebhookAnnotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive real-time annotation webhook payload",
)
async def receive_annotation_webhook(
    payload: WebhookAnnotationPayload,
    db: Session = Depends(get_db),
):
    """
    Receive real-time annotation data from external annotation tools,
    validate payload constraints, ingest into the database, and trigger Trust Score calculation.
    """
    try:
        result = process_webhook_annotation(db=db, payload=payload)
        return result

    except DuplicateAnnotationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )
    except WebhookIngestionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook ingestion error: {str(exc)}",
        )
