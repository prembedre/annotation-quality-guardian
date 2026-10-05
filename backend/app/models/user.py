"""
User model representing platform users with role-based access control.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String

from app.core.db import Base


class UserRole(str, enum.Enum):
    """Roles available in the AQG platform."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    REVIEWER = "reviewer"
    ANNOTATOR = "annotator"


class User(Base):
    """
    Platform user account with an assigned role.

    The role determines which API routes and UI elements
    are accessible to this user.
    """

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(
        String(255),
        nullable=False,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        Enum(UserRole, name="userrole", create_type=True),
        nullable=False,
        default=UserRole.ANNOTATOR,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
