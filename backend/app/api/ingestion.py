"""
API endpoints for data ingestion.
"""

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.ingestion_service import ingest_file


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or JSON file and ingest its annotation data.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in {".csv", ".json"}:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and JSON files are supported.",
        )

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        result = ingest_file(
            db=db,
            file_path=temp_file_path,
        )

        return {
            "message": "File ingestion completed.",
            "filename": file.filename,
            "result": result,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(exc)}",
        )

    finally:
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
