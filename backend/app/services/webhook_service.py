"""
Webhook Ingestion Service.
Processes incoming real-time annotation payloads from external annotation tools,
validates project/annotator references, integrates with the existing ingestion
pipeline and database models, and triggers Trust Score recalculation.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.annotator import Annotator
from app.models.item import Item
from app.models.annotation import Annotation
from app.schemas.webhook import WebhookAnnotationPayload
from app.services.trust_score_service import compute_and_save_item_trust_score


class WebhookIngestionError(Exception):
    """Custom exception for webhook validation or ingestion failures."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DuplicateAnnotationError(WebhookIngestionError):
    """Exception raised when an identical annotation already exists."""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


def process_webhook_annotation(
    db: Session,
    payload: WebhookAnnotationPayload,
) -> Dict[str, Any]:
    """
    Ingest a single real-time annotation payload from an external webhook.

    Pipeline:
    1. Verify project exists
    2. Verify/auto-register annotator
    3. Validate label against project label_set constraints if defined
    4. Find or create item record
    5. Check for duplicate annotation (item_id, annotator_id)
    6. Insert annotation record
    7. Trigger Trust Score calculation for the item
    8. Commit transaction and return summary
    """
    # 1. Verify project exists
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise WebhookIngestionError(
            f"Project with ID {payload.project_id} not found.",
            status_code=404,
        )

    # 2. Check label_set constraints if configured
    if project.label_set and isinstance(project.label_set, list) and len(project.label_set) > 0:
        if payload.label not in project.label_set:
            raise WebhookIngestionError(
                f"Label '{payload.label}' is not in project's allowed label_set: {project.label_set}",
                status_code=400,
            )

    # 3. Ensure annotator exists or auto-register
    annotator = db.query(Annotator).filter(Annotator.id == payload.annotator_id).first()
    if not annotator:
        annotator = Annotator(
            id=payload.annotator_id,
            username=f"Annotator_{payload.annotator_id}",
        )
        db.add(annotator)
        db.flush()

    try:
        # 4. Find or create item
        item = (
            db.query(Item)
            .filter(
                Item.project_id == payload.project_id,
                Item.external_id == payload.item_id,
            )
            .first()
        )

        if item is None:
            content = payload.content if payload.content else {"item_id": payload.item_id}
            item = Item(
                project_id=payload.project_id,
                external_id=payload.item_id,
                content=content,
                source=f"webhook_project_{payload.project_id}",
            )
            db.add(item)
            db.flush()

        # 5. Check for duplicate annotation
        existing_annotation = (
            db.query(Annotation)
            .filter(
                Annotation.item_id == item.id,
                Annotation.annotator_id == payload.annotator_id,
            )
            .first()
        )

        if existing_annotation is not None:
            raise DuplicateAnnotationError(
                f"Annotation already exists for item '{payload.item_id}' and annotator {payload.annotator_id}."
            )

        # 6. Insert new annotation
        new_annotation = Annotation(
            project_id=payload.project_id,
            item_id=item.id,
            annotator_id=payload.annotator_id,
            label=payload.label.strip(),
            confidence=payload.confidence,
            duration_ms=payload.duration_ms,
            metadata_=payload.metadata or {},
        )
        db.add(new_annotation)
        db.flush()

        # 7. Trigger Trust Score calculation for this item
        trust_score_rec = compute_and_save_item_trust_score(
            db=db,
            project_id=payload.project_id,
            item_id=item.id,
        )

        db.commit()
        db.refresh(new_annotation)

        return {
            "success": True,
            "message": "Annotation ingested and trust score computed successfully.",
            "project_id": payload.project_id,
            "item_id": item.id,
            "external_id": item.external_id,
            "annotation_id": new_annotation.id,
            "trust_score": float(trust_score_rec.final_score) if trust_score_rec and trust_score_rec.final_score is not None else None,
            "flagged": trust_score_rec.flagged if trust_score_rec else False,
            "is_duplicate": False,
        }

    except WebhookIngestionError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise WebhookIngestionError(
            f"Failed to ingest webhook annotation: {str(exc)}",
            status_code=500,
        )
