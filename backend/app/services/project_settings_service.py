"""
Project Settings Service.

Manages project-level quality thresholds and Phase 4 automation controls.
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_threshold import ProjectThreshold


DEFAULT_PROJECT_SETTINGS: Dict[str, Any] = {
    "gold_threshold": 90.0,
    "kappa_threshold": 0.7,
    "behavior_threshold": 75.0,
    "embedding_threshold": 80.0,
    "automation_enabled": True,
}


def _get_project(
    db: Session,
    project_id: int,
) -> Project:
    """
    Retrieve a project or raise a clear error when it does not exist.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise ValueError(
            f"Project with ID {project_id} not found."
        )

    return project


def _get_or_create_thresholds(
    db: Session,
    project_id: int,
) -> ProjectThreshold:
    """
    Retrieve the project's threshold configuration.

    If the project does not have a threshold row yet, create one
    using the Phase 3 default values.
    """

    thresholds = (
        db.query(ProjectThreshold)
        .filter(ProjectThreshold.project_id == project_id)
        .first()
    )

    if thresholds is None:
        thresholds = ProjectThreshold(
            project_id=project_id,
            gold_threshold=DEFAULT_PROJECT_SETTINGS["gold_threshold"] / 100.0,
            kappa_threshold=DEFAULT_PROJECT_SETTINGS["kappa_threshold"],
            behavioral_threshold=DEFAULT_PROJECT_SETTINGS["behavior_threshold"] / 100.0,
            embedding_threshold=DEFAULT_PROJECT_SETTINGS["embedding_threshold"] / 100.0,
            trust_threshold=0.60,
        )

        db.add(thresholds)
        db.flush()

    return thresholds


def get_project_settings(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """
    Retrieve project quality thresholds and persistent automation settings.
    """

    project = _get_project(
        db=db,
        project_id=project_id,
    )

    thresholds = _get_or_create_thresholds(
        db=db,
        project_id=project_id,
    )

    db.commit()

    return {
        "project_id": project.id,
        "gold_threshold": float(thresholds.gold_threshold) * 100.0,
        "kappa_threshold": float(thresholds.kappa_threshold),
        "behavior_threshold": float(thresholds.behavioral_threshold) * 100.0,
        "embedding_threshold": float(thresholds.embedding_threshold) * 100.0,
        "automation_enabled": bool(
            project.automation_enabled
        ),
    }


def update_project_settings(
    db: Session,
    project_id: int,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update project quality thresholds and persistent automation controls.
    """

    project = _get_project(
        db=db,
        project_id=project_id,
    )

    thresholds = _get_or_create_thresholds(
        db=db,
        project_id=project_id,
    )

    if "gold_threshold" in updates:
        thresholds.gold_threshold = float(
            updates["gold_threshold"]
        ) / 100.0

    if "kappa_threshold" in updates:
        thresholds.kappa_threshold = float(
            updates["kappa_threshold"]
        )

    if "behavior_threshold" in updates:
        thresholds.behavioral_threshold = float(
            updates["behavior_threshold"]
        ) / 100.0

    if "embedding_threshold" in updates:
        thresholds.embedding_threshold = float(
            updates["embedding_threshold"]
        ) / 100.0

    if "automation_enabled" in updates:
        automation_value = updates["automation_enabled"]

        if automation_value is not None:
            project.automation_enabled = bool(
                automation_value
            )

    db.commit()
    db.refresh(project)
    db.refresh(thresholds)

    return get_project_settings(
        db=db,
        project_id=project_id,
    )