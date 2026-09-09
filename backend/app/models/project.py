"""
Project model representing an annotation dataset/task project.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class Project(Base):
    """
    Represents an annotation project with a defined label set.
    """

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    label_set = Column(
        JSON,
        nullable=False,
        default=list,
        doc="List of valid label strings",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
    )

    automation_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether Phase 4 automation is enabled for this project",
    )

    # Relationships

    items = relationship(
        "Item",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    annotations = relationship(
        "Annotation",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    trust_scores = relationship(
        "TrustScore",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    behavioral_scores = relationship(
        "BehavioralScore",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    embedding_results = relationship(
        "EmbeddingResult",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    threshold = relationship(
        "ProjectThreshold",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )

    reviewer_decisions = relationship(
        "ReviewerDecision",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    reroute_histories = relationship(
        "RerouteHistory",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    ab_test_experiments = relationship(
        "ABTestExperiment",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
