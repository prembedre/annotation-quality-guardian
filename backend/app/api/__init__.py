"""
API routes module init.
"""

from app.api import health, annotations, projects, scores, review, export, ingestion, jobs

__all__ = [
    "health",
    "annotations",
    "projects",
    "scores",
    "review",
    "export",
    "ingestion",
    "jobs",
]
