"""
API endpoints for data ingestion.
"""

import os
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.ingestion import IngestionResponse
from app.services.ingestion_service import ingest_file

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post("/upload", response_model=IngestionResponse)
async def upload_file(
    file: UploadFile = File(..., description="CSV or JSON file"),
    project_id: Optional[int] = Form(None, description="Optional target project ID"),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or JSON file and ingest its annotation data into PostgreSQL.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in {".csv", ".json"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Only CSV and JSON files are supported.",
        )

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            content = await file.read()
            if not content or len(content.strip()) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            temp_file.write(content)
            temp_file_path = temp_file.name

        result = ingest_file(
            db=db,
            file_path=temp_file_path,
            default_project_id=project_id,
        )
        result["filename"] = file.filename
        return result

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(exc)}",
        )
    finally:
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
