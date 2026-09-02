"""
Project Settings Service.
Manages reading and updating project-level quality scoring thresholds.
Provides a clean service abstraction decoupling API logic from Member 2's database schema migrations.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.project import Project

# Default quality scoring thresholds
DEFAULT_PROJECT_SETTINGS: Dict[str, Any] = {
    "gold_threshold": 90.0,
    "kappa_threshold": 0.7,
    "behavior_threshold": 75.0,
    "embedding_threshold": 80.0,
}

# In-memory settings storage cache (backed by service interface until Member 2 completes DB migration)
_PROJECT_SETTINGS_STORE: Dict[int, Dict[str, Any]] = {}


def get_project_settings(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """
    Retrieve quality scoring thresholds for a specific project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found.")

    if project_id not in _PROJECT_SETTINGS_STORE:
        # Initialize with defaults
        _PROJECT_SETTINGS_STORE[project_id] = dict(DEFAULT_PROJECT_SETTINGS)

    settings = dict(_PROJECT_SETTINGS_STORE[project_id])
    settings["project_id"] = project_id
    return settings


def update_project_settings(
    db: Session,
    project_id: int,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update quality scoring thresholds for a specific project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found.")

    if project_id not in _PROJECT_SETTINGS_STORE:
        _PROJECT_SETTINGS_STORE[project_id] = dict(DEFAULT_PROJECT_SETTINGS)

    current_settings = _PROJECT_SETTINGS_STORE[project_id]

    for key, value in updates.items():
        if value is not None and key in DEFAULT_PROJECT_SETTINGS:
            current_settings[key] = float(value)

    res = dict(current_settings)
    res["project_id"] = project_id
    return res
