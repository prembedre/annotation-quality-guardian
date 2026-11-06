"""
AutomationRule model for project-level automation policies.
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db import Base


class AutomationRule(Base):
    """
    Represents an automation policy rule configured for a project.
    """

    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    condition = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("project_id", "rule_id", name="uq_project_rule"),
    )

    project = relationship("Project", backref="automation_rules")
