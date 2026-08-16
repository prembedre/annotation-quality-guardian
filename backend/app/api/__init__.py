"""
API routes module init.
"""

from app.api import health, annotations, projects, scores

__all__ = ["health", "annotations", "projects", "scores"]
