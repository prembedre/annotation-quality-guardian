"""
Data ingestion service for CSV and JSON annotation data.

Pipeline Flow:
CSV / JSON
    -> Read & parse
    -> Validate structure & types
    -> Validate project existence & label_set constraints
    -> Normalize fields (trim strings, casts, metadata)
    -> Detect in-batch duplicates (project_id, external_id, annotator_id)
    -> Check database duplicates
    -> Upsert/Insert items and annotations
    -> Commit transaction safely
    -> Return structured summary with error diagnostics
"""

import csv
import json
from pathlib import Path
from typing import Any, Optional, Dict, List

from sqlalchemy.orm import Session

from app.models.annotation import Annotation
from app.models.item import Item
from app.models.annotator import Annotator
from app.models.project import Project


def read_csv(file_path: str) -> List[Dict[str, Any]]:
    """Read annotation records from a CSV file."""
    with open(file_path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def read_json(file_path: str) -> List[Dict[str, Any]]:
    """Read annotation records from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        if "annotations" in data and isinstance(data["annotations"], list):
            data = data["annotations"]
        elif "items" in data and isinstance(data["items"], list):
            data = data["items"]
        elif "data" in data and isinstance(data["data"], list):
            data = data["data"]
        else:
            data = [data]

    if not isinstance(data, list):
        raise ValueError("JSON data must be a list of annotation records or an object containing an 'annotations' list.")

    return data


def read_file(file_path: str) -> List[Dict[str, Any]]:
    """Read CSV or JSON based on the file extension."""
    extension = Path(file_path).suffix.lower()

    if extension == ".csv":
        return read_csv(file_path)
    if extension == ".json":
        return read_json(file_path)

    raise ValueError("Only CSV and JSON files are supported.")


def validate_and_normalize_record(
    record: Dict[str, Any],
    default_project_id: Optional[int] = None,
    valid_labels_by_project: Optional[Dict[int, List[str]]] = None,
) -> tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Validate and normalize a single incoming annotation record.

    Returns (normalized_record, error_list).
    """
    errors: List[str] = []
    normalized: Dict[str, Any] = {}

    # 1. Project ID resolution & validation
    raw_project_id = record.get("project_id") or default_project_id
    if raw_project_id is None or str(raw_project_id).strip() == "":
        errors.append("Missing required field: project_id")
        project_id = None
    else:
        try:
            project_id = int(raw_project_id)
            normalized["project_id"] = project_id
        except (TypeError, ValueError):
            errors.append("project_id must be an integer")
            project_id = None

    # 2. Item ID / External ID resolution
    raw_ext_id = record.get("external_id") or record.get("item_id")
    if raw_ext_id is None or str(raw_ext_id).strip() == "":
        errors.append("Missing required field: item_id or external_id")
    else:
        normalized["external_id"] = str(raw_ext_id).strip()

    # 3. Annotator ID
    raw_annotator_id = record.get("annotator_id")
    if raw_annotator_id is None or str(raw_annotator_id).strip() == "":
        errors.append("Missing required field: annotator_id")
    else:
        try:
            normalized["annotator_id"] = int(raw_annotator_id)
        except (TypeError, ValueError):
            errors.append("annotator_id must be an integer")

    # 4. Label & label_set check
    raw_label = record.get("label")
    if raw_label is None or str(raw_label).strip() == "":
        errors.append("Missing required field: label")
    else:
        clean_label = str(raw_label).strip()
        normalized["label"] = clean_label

        # Validate against project's allowed label_set if configured
        if project_id and valid_labels_by_project and project_id in valid_labels_by_project:
            allowed = valid_labels_by_project[project_id]
            if allowed and clean_label not in allowed:
                errors.append(f"Label '{clean_label}' is not in project's allowed label_set: {allowed}")

    # 5. Confidence
    raw_confidence = record.get("confidence")
    if raw_confidence not in (None, ""):
        try:
            conf_val = float(raw_confidence)
            if not 0.0 <= conf_val <= 1.0:
                errors.append("confidence must be between 0.0 and 1.0")
            else:
                normalized["confidence"] = conf_val
        except (TypeError, ValueError):
            errors.append("confidence must be a valid float between 0.0 and 1.0")
    else:
        normalized["confidence"] = None

    # 6. Duration
    raw_duration = record.get("duration_ms")
    if raw_duration not in (None, ""):
        try:
            dur_val = int(raw_duration)
            if dur_val < 0:
                errors.append("duration_ms cannot be negative")
            else:
                normalized["duration_ms"] = dur_val
        except (TypeError, ValueError):
            errors.append("duration_ms must be an integer")
    else:
        normalized["duration_ms"] = None

    # 7. Content (text/metadata of the item)
    content = record.get("content")
    if content in (None, ""):
        # Default content with external_id
        normalized["content"] = {"item_id": normalized.get("external_id", "unknown")}
    elif isinstance(content, str):
        content_str = content.strip()
        try:
            normalized["content"] = json.loads(content_str)
        except json.JSONDecodeError:
            normalized["content"] = {"text": content_str}
    elif isinstance(content, dict):
        normalized["content"] = content
    else:
        normalized["content"] = {"raw": str(content)}

    # 8. Metadata
    metadata = record.get("metadata")
    if metadata in (None, ""):
        normalized["metadata"] = {}
    elif isinstance(metadata, str):
        try:
            normalized["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            normalized["metadata"] = {"raw": metadata}
    elif isinstance(metadata, dict):
        normalized["metadata"] = metadata
    else:
        normalized["metadata"] = {}

    if errors:
        return None, errors
    return normalized, []


def ingest_file(
    db: Session,
    file_path: str,
    default_project_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Complete CSV/JSON ingestion pipeline.

    Steps:
    1. Read and parse file
    2. Check empty file
    3. Load project cache for label validation
    4. Validate and normalize each record
    5. Deduplicate within file batch
    6. Deduplicate against PostgreSQL database
    7. Insert items, annotators (auto-create if missing), and annotations
    8. Commit transaction
    """
    records = read_file(file_path)

    if not records:
        return {
            "success": False,
            "message": "The uploaded file contains no records.",
            "total_records": 0,
            "inserted_records": 0,
            "duplicate_records": 0,
            "failed_records": 0,
            "errors": [{"row": 0, "error": "Empty file"}],
        }

    # Pre-cache project label sets
    projects = db.query(Project).all()
    project_label_sets = {p.id: p.label_set for p in projects if p.label_set}
    existing_project_ids = {p.id for p in projects}

    inserted = 0
    skipped_duplicates = 0
    errors: List[Dict[str, Any]] = []

    seen_batch_keys = set()
    valid_normalized_records: List[tuple[int, Dict[str, Any]]] = []

    # First pass: Validate and detect in-batch duplicates
    for idx, raw_record in enumerate(records):
        row_num = idx + 1
        normalized, record_errors = validate_and_normalize_record(
            record=raw_record,
            default_project_id=default_project_id,
            valid_labels_by_project=project_label_sets,
        )

        if record_errors:
            errors.append({
                "row": row_num,
                "errors": record_errors,
            })
            continue

        proj_id = normalized["project_id"]
        # If projects exist in DB, verify project existence
        if existing_project_ids and proj_id not in existing_project_ids:
            errors.append({
                "row": row_num,
                "error": f"Project ID {proj_id} does not exist",
            })
            continue

        # In-batch duplicate key: (project_id, external_id, annotator_id)
        batch_key = (proj_id, normalized["external_id"], normalized["annotator_id"])
        if batch_key in seen_batch_keys:
            skipped_duplicates += 1
            errors.append({
                "row": row_num,
                "error": f"Duplicate annotation in uploaded file for item '{normalized['external_id']}' and annotator {normalized['annotator_id']}",
            })
            continue

        seen_batch_keys.add(batch_key)
        valid_normalized_records.append((row_num, normalized))

    try:
        # Pre-cache annotators and items to minimize round-trips
        existing_annotators = {a.id: a for a in db.query(Annotator).all()}

        for row_num, norm in valid_normalized_records:
            proj_id = norm["project_id"]
            ext_id = norm["external_id"]
            ann_id = norm["annotator_id"]

            # Ensure annotator exists or auto-register
            if ann_id not in existing_annotators:
                annotator = Annotator(id=ann_id, name=f"Annotator_{ann_id}")
                db.add(annotator)
                db.flush()
                existing_annotators[ann_id] = annotator

            # Find or create item
            item = (
                db.query(Item)
                .filter(
                    Item.project_id == proj_id,
                    Item.external_id == ext_id,
                )
                .first()
            )

            if item is None:
                item = Item(
                    project_id=proj_id,
                    external_id=ext_id,
                    content=norm["content"],
                    source=f"project_{proj_id}",
                )
                db.add(item)
                db.flush()

            # Check DB duplicate
            existing_annotation = (
                db.query(Annotation)
                .filter(
                    Annotation.item_id == item.id,
                    Annotation.annotator_id == ann_id,
                )
                .first()
            )

            if existing_annotation is not None:
                skipped_duplicates += 1
                errors.append({
                    "row": row_num,
                    "error": f"Annotation already exists in database for item '{ext_id}' and annotator {ann_id}",
                })
                continue

            # Insert annotation
            new_annotation = Annotation(
                project_id=proj_id,
                item_id=item.id,
                annotator_id=ann_id,
                label=norm["label"],
                confidence=norm["confidence"],
                duration_ms=norm["duration_ms"],
                metadata_=norm["metadata"],
            )
            db.add(new_annotation)
            inserted += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Ingestion processed: {inserted} inserted, {skipped_duplicates} duplicate(s) skipped, {len(errors) - skipped_duplicates} error(s).",
        "total_records": len(records),
        "inserted_records": inserted,
        "duplicate_records": skipped_duplicates,
        "failed_records": len(errors) - skipped_duplicates,
        "errors": errors,
    }
