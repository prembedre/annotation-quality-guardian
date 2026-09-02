"""
ProjectThreshold model representing project-specific quality scoring thresholds.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class ProjectThreshold(Base):
    """
    Represents quality scoring threshold settings configured per project.
    """

    __tablename__ = "project_thresholds"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="Foreign key to projects table (one threshold config per project)",
    )

    gold_threshold = Column(
        Numeric(10, 6),
        nullable=False,
        default=0.90,
        doc="Gold accuracy threshold (0.0 to 1.0 or percentage)",
    )

    kappa_threshold = Column(
        Numeric(10, 6),
        nullable=False,
        default=0.70,
        doc="Cohen/Fleiss Kappa inter-annotator agreement threshold",
    )

    behavioral_threshold = Column(
        Numeric(10, 6),
        nullable=False,
        default=0.75,
        doc="Behavioral score threshold",
    )

    embedding_threshold = Column(
        Numeric(10, 6),
        nullable=False,
        default=0.80,
        doc="Embedding outlier threshold",
    )

    trust_threshold = Column(
        Numeric(10, 6),
        nullable=False,
        default=0.60,
        doc="Trust score flagging threshold below which items are flagged",
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

    # Relationships

    project = relationship(
        "Project",
        back_populates="threshold",
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectThreshold("
            f"id={self.id}, "
            f"project_id={self.project_id}, "
            f"gold={self.gold_threshold}, "
            f"trust={self.trust_threshold}"
            f")>"
        )
