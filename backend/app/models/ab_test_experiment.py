"""
ABTestExperiment model representing label schema and guideline A/B testing experiments.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class ABTestExperiment(Base):
    """
    Represents an A/B testing experiment for comparing annotation schemas,
    guideline variants, or annotator group performance.
    """

    __tablename__ = "ab_test_experiments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    experiment_name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Human-readable title/name of the experiment",
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target project ID",
    )

    schema_version_a = Column(
        JSON,
        nullable=False,
        default=dict,
        doc="Control schema configuration (e.g. labels, instructions, guidelines)",
    )

    schema_version_b = Column(
        JSON,
        nullable=False,
        default=dict,
        doc="Variant schema configuration to test",
    )

    annotator_group = Column(
        JSON,
        nullable=True,
        default=dict,
        doc="Annotator allocation rules or group segmentation mapping",
    )

    assigned_version = Column(
        String(50),
        nullable=True,
        doc="Default or active variant code ('A', 'B', or 'SPLIT_50_50')",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        doc="Experiment lifecycle status: 'active', 'completed', 'draft'",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when experiment was concluded",
    )

    # Relationships
    project = relationship(
        "Project",
        back_populates="ab_test_experiments",
    )

    def __repr__(self) -> str:
        return (
            f"<ABTestExperiment("
            f"id={self.id}, "
            f"name='{self.experiment_name}', "
            f"project_id={self.project_id}, "
            f"status='{self.status}'"
            f")>"
        )
