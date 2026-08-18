"""
API routes module init.
"""

from app.api import health, annotations, projects, scores, review, export, ingestion

__all__ = [
    "health",
    "annotations",
    "projects",
    "scores",
    "review",
    "export",
    "ingestion",
]
