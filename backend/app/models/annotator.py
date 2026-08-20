"""
Annotator model representing human or model annotators.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.db import Base


class Annotator(Base):
    """
    Represents an annotator providing labels.
    """

    __tablename__ = "annotators"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    email = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    annotations = relationship(
        "Annotation",
        back_populates="annotator",
        cascade="all, delete-orphan",
    )

    behavioral_scores = relationship(
        "BehavioralScore",
        back_populates="annotator",
        cascade="all, delete-orphan",
    )

    def __init__(self, *args, **kwargs):
        if "name" in kwargs and "username" not in kwargs:
            kwargs["username"] = kwargs.pop("name")
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        """Alias for username to preserve backwards compatibility."""
        return self.username

    @name.setter
    def name(self, value: str):
        self.username = value

    def __repr__(self) -> str:
        return f"<Annotator(id={self.id}, username='{self.username}')>"
