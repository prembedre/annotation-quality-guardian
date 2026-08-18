"""
API routes for exporting project annotation datasets with attached trust scores.
"""

import io
import csv
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Project, Item, Annotation, Annotator, TrustScore
from app.schemas.export import DatasetExportResponse, DatasetExportItem, ExportItemAnnotation

router = APIRouter()


@router.get("/{project_id}/export", summary="Export dataset with trust scores")
async def export_project_dataset(
    project_id: int,
    format: str = Query("csv", description="Output format: 'csv' or 'json'"),
    db: Session = Depends(get_db),
):
    """
    Export all items, annotations, and quality/trust score metrics for a given project.
    Supports downloadable CSV or structured JSON.
    """
    # 1. Validate project existence
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found",
        )

    # 2. Validate format
    fmt = format.lower().strip()
    if fmt not in {"csv", "json"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Supported formats are 'csv' and 'json'.",
        )

    # 3. Query items and annotations for the project
    items = db.query(Item).filter(Item.project_id == project_id).all()
    annotators_map = {a.id: a.name for a in db.query(Annotator).all()}

    # 4. Handle CSV Export
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "project_id",
            "project_name",
            "item_id",
            "external_id",
            "is_gold",
            "gold_label",
            "trust_score",
            "flagged",
            "annotation_id",
            "annotator_id",
            "annotator_name",
            "annotation_label",
            "confidence",
            "duration_ms",
            "annotation_created_at",
        ])

        total_rows = 0
        for item in items:
            ts = db.query(TrustScore).filter(TrustScore.item_id == item.id).first()
            trust_score_val = ts.score if ts else ""
            is_flagged = ts.flagged if ts else False

            if item.annotations:
                for ann in item.annotations:
                    writer.writerow([
                        project.id,
                        project.name,
                        item.id,
                        item.external_id or "",
                        item.is_gold,
                        item.gold_label or "",
                        trust_score_val,
                        is_flagged,
                        ann.id,
                        ann.annotator_id,
                        annotators_map.get(ann.annotator_id, f"Annotator {ann.annotator_id}"),
                        ann.label,
                        ann.confidence if ann.confidence is not None else "",
                        ann.duration_ms if ann.duration_ms is not None else "",
                        ann.created_at.isoformat() if ann.created_at else "",
                    ])
                    total_rows += 1
            else:
                # Item without annotations
                writer.writerow([
                    project.id,
                    project.name,
                    item.id,
                    item.external_id or "",
                    item.is_gold,
                    item.gold_label or "",
                    trust_score_val,
                    is_flagged,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ])
                total_rows += 1

        output.seek(0)
        filename = f"project_{project_id}_export.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # 5. Handle JSON Export
    items_out = []
    total_annotations = 0

    for item in items:
        ts = db.query(TrustScore).filter(TrustScore.item_id == item.id).first()
        trust_score_val = ts.score if ts else None
        trust_breakdown = ts.breakdown if ts else {}
        is_flagged = ts.flagged if ts else False

        annotations_out = []
        for ann in item.annotations:
            annotations_out.append(
                ExportItemAnnotation(
                    annotation_id=ann.id,
                    annotator_id=ann.annotator_id,
                    annotator_name=annotators_map.get(ann.annotator_id, f"Annotator {ann.annotator_id}"),
                    label=ann.label,
                    confidence=ann.confidence,
                    duration_ms=ann.duration_ms,
                    metadata=ann.metadata_ or {},
                    created_at=ann.created_at,
                )
            )
            total_annotations += 1

        items_out.append(
            DatasetExportItem(
                item_id=item.id,
                external_id=item.external_id or str(item.id),
                content=item.content or {},
                is_gold=item.is_gold,
                gold_label=item.gold_label,
                trust_score=trust_score_val,
                trust_score_breakdown=trust_breakdown,
                flagged=is_flagged,
                annotations=annotations_out,
            )
        )

    response_data = DatasetExportResponse(
        project_id=project.id,
        project_name=project.name,
        total_items=len(items_out),
        total_annotations=total_annotations,
        items=items_out,
    )
    return response_data
