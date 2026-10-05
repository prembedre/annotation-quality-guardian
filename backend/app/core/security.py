"""
Security utilities: password hashing, JWT creation/verification, and role permissions.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import UserRole


# ── Password Hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(plain_password)


# ── JWT Token Helpers ─────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict (should include ``sub`` claim with user email).
        expires_delta: Override the default expiry window.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Raises:
        jose.JWTError: if the token is invalid, expired, or tampered with.

    Returns:
        Decoded payload dict.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── Role → Permission Mapping ─────────────────────────────────────────────────

ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.ADMIN: {
        "manage_users",
        "manage_projects",
        "manage_settings",
        "view_dashboard",
        "review_items",
        "annotate_items",
        "run_automation",
        "run_ab_tests",
        "manage_integrations",
        "manage_export",
        "trigger_jobs",
    },
    UserRole.PROJECT_MANAGER: {
        "manage_projects",
        "manage_settings",
        "view_dashboard",
        "review_items",
        "run_automation",
        "run_ab_tests",
        "manage_export",
        "trigger_jobs",
    },
    UserRole.REVIEWER: {
        "view_dashboard",
        "review_items",
        "manage_export",
    },
    UserRole.ANNOTATOR: {
        "annotate_items",
    },
}


def has_permission(role: UserRole, permission: str) -> bool:
    """Return True if the given role includes the requested permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
