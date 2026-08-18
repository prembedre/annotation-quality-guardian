"""
Data ingestion service for CSV and JSON annotation data.

Flow:
CSV/JSON
    -> Read
    -> Validate
    -> Normalize
    -> Detect duplicates
    -> Check database duplicates
    -> Insert items and annotations
    -> Commit transaction
"""

import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.annotation import Annotation
from app.models.item import Item


# Required fields for each incoming annotation record.
REQUIRED_FIELDS = {
    "project_id",
    "external_id",
    "content",
    "annotator_id",
    "label",
}


def read_csv(file_path: str) -> list[dict[str, Any]]:
    """Read annotation records from a CSV file."""

    with open(file_path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_json(file_path: str) -> list[dict[str, Any]]:
    """Read annotation records from a JSON file."""

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Allow JSON format:
    # {"annotations": [...]}
    if isinstance(data, dict):
        data = data.get("annotations", [])

    if not isinstance(data, list):
        raise ValueError(
            "JSON data must contain a list of annotation records."
        )

    return data


def read_file(file_path: str) -> list[dict[str, Any]]:
    """Read CSV or JSON based on the file extension."""

    extension = Path(file_path).suffix.lower()

    if extension == ".csv":
        return read_csv(file_path)

    if extension == ".json":
        return read_json(file_path)

    raise ValueError("Only CSV and JSON files are supported.")


def validate_record(record: dict[str, Any]) -> list[str]:
    """
    Validate one incoming annotation record.

    Returns a list of validation errors.
    An empty list means the record is valid.
    """

    errors = []

    # Check required fields.
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, ""):
            errors.append(f"Missing required field: {field}")

    # Validate project_id.
    project_id = record.get("project_id")

    if project_id not in (None, ""):
        try:
            int(project_id)
        except (TypeError, ValueError):
            errors.append("project_id must be an integer")

    # Validate annotator_id.
    annotator_id = record.get("annotator_id")

    if annotator_id not in (None, ""):
        try:
            int(annotator_id)
        except (TypeError, ValueError):
            errors.append("annotator_id must be an integer")

    # Validate confidence.
    confidence = record.get("confidence")

    if confidence not in (None, ""):
        try:
            confidence = float(confidence)

            if not 0 <= confidence <= 1:
                errors.append("confidence must be between 0 and 1")

        except (TypeError, ValueError):
            errors.append("confidence must be a number")

    # Validate duration.
    duration_ms = record.get("duration_ms")

    if duration_ms not in (None, ""):
        try:
            if int(duration_ms) < 0:
                errors.append("duration_ms cannot be negative")

        except (TypeError, ValueError):
            errors.append("duration_ms must be an integer")

    return errors


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize an incoming record before database insertion.
    """

    normalized = dict(record)

    # Convert IDs to integers.
    normalized["project_id"] = int(normalized["project_id"])
    normalized["annotator_id"] = int(normalized["annotator_id"])

    # Clean text fields.
    normalized["external_id"] = str(
        normalized["external_id"]
    ).strip()

    normalized["label"] = str(
        normalized["label"]
    ).strip()

    # Normalize confidence.
    confidence = normalized.get("confidence")

    if confidence in (None, ""):
        normalized["confidence"] = None
    else:
        normalized["confidence"] = float(confidence)

    # Normalize duration.
    duration_ms = normalized.get("duration_ms")

    if duration_ms in (None, ""):
        normalized["duration_ms"] = None
    else:
        normalized["duration_ms"] = int(duration_ms)

    # Normalize metadata.
    metadata = normalized.get("metadata")

    if metadata in (None, ""):
        normalized["metadata"] = {}

    elif isinstance(metadata, str):
        try:
            normalized["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            normalized["metadata"] = {
                "raw": metadata
            }

    # Normalize content.
    content = normalized.get("content")

    if isinstance(content, str):
        content = content.strip()

        try:
            normalized["content"] = json.loads(content)
        except json.JSONDecodeError:
            normalized["content"] = {
                "text": content
            }

    return normalized


def find_duplicate_records(
    records: list[dict[str, Any]],
) -> list[int]:
    """
    Find duplicate records inside the uploaded file.

    A duplicate is identified using:
    project_id + external_id + annotator_id

    Returns the indexes of duplicate records.
    """

    seen = set()
    duplicate_indexes = []

    for index, record in enumerate(records):
        key = (
            record["project_id"],
            record["external_id"],
            record["annotator_id"],
        )

        if key in seen:
            duplicate_indexes.append(index)
        else:
            seen.add(key)

    return duplicate_indexes


def annotation_exists(
    db: Session,
    project_id: int,
    external_id: str,
    annotator_id: int,
) -> bool:
    """
    Check whether an annotation already exists in PostgreSQL.
    """

    item = (
        db.query(Item)
        .filter(
            Item.project_id == project_id,
            Item.external_id == external_id,
        )
        .first()
    )

    if item is None:
        return False

    annotation = (
        db.query(Annotation)
        .filter(
            Annotation.item_id == item.id,
            Annotation.annotator_id == annotator_id,
        )
        .first()
    )

    return annotation is not None


def insert_annotation(
    db: Session,
    record: dict[str, Any],
) -> Annotation:
    """
    Insert an item and its annotation into PostgreSQL.
    """

    # Find existing item.
    item = (
        db.query(Item)
        .filter(
            Item.project_id == record["project_id"],
            Item.external_id == record["external_id"],
        )
        .first()
    )

    # Create item if it does not exist.
    if item is None:
        item = Item(
            project_id=record["project_id"],
            external_id=record["external_id"],
            content=record["content"],
        )

        db.add(item)
        db.flush()

    # Create annotation.
    annotation = Annotation(
        project_id=record["project_id"],
        item_id=item.id,
        annotator_id=record["annotator_id"],
        label=record["label"],
        confidence=record.get("confidence"),
        duration_ms=record.get("duration_ms"),
        metadata=record.get("metadata", {}),
    )

    db.add(annotation)
    db.flush()

    return annotation


def ingest_file(
    db: Session,
    file_path: str,
) -> dict[str, Any]:
    """
    Complete CSV/JSON ingestion pipeline.

    Steps:
    1. Read file
    2. Validate records
    3. Normalize records
    4. Detect duplicates inside the file
    5. Check duplicates in PostgreSQL
    6. Insert valid records
    7. Commit transaction
    """

    records = read_file(file_path)

    inserted = 0
    skipped_duplicates = 0
    errors = []

    # Track duplicates inside uploaded file.
    duplicate_indexes = set(
        find_duplicate_records(records)
    )

    try:
        for index, record in enumerate(records):

            # Skip duplicate inside uploaded file.
            if index in duplicate_indexes:
                skipped_duplicates += 1

                errors.append({
                    "row": index + 1,
                    "error": "Duplicate record in uploaded file",
                })

                continue

            # Validate record.
            validation_errors = validate_record(record)

            if validation_errors:
                errors.append({
                    "row": index + 1,
                    "errors": validation_errors,
                })

                continue

            # Normalize record.
            normalized = normalize_record(record)

            # Check PostgreSQL duplicate.
            if annotation_exists(
                db=db,
                project_id=normalized["project_id"],
                external_id=normalized["external_id"],
                annotator_id=normalized["annotator_id"],
            ):
                skipped_duplicates += 1

                errors.append({
                    "row": index + 1,
                    "error": "Annotation already exists in database",
                })

                continue

            # Insert into PostgreSQL.
            insert_annotation(
                db=db,
                record=normalized,
            )

            inserted += 1

        # Commit all successful inserts.
        db.commit()

    except Exception:
        # Roll back if something unexpected happens.
        db.rollback()
        raise

    return {
        "total_records": len(records),
        "inserted": inserted,
        "skipped_duplicates": skipped_duplicates,
        "errors": errors,
  }
