"""
API routes module init.
"""

from app.api import health, annotations, projects, scores, review, export, ingestion, jobs, webhook, dashboard, project_settings

__all__ = [
    "health",
    "annotations",
    "projects",
    "scores",
    "review",
    "export",
    "ingestion",
    "jobs",
    "webhook",
    "dashboard",
    "project_settings",
]

