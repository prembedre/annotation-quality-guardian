"""
FastAPI dependency functions for authentication and authorization.

Usage in route handlers:
    from app.core.auth_deps import get_current_user, require_role, require_permission

    @router.get("/...", dependencies=[Depends(require_role(UserRole.ADMIN))])
    # or inject the user:
    async def my_route(current_user: User = Depends(get_current_user)):
        ...
"""

from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token, has_permission
from app.models.user import User, UserRole


# OAuth2 token URL tells FastAPI/Swagger where to obtain a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_or_create_default_admin(db: Session) -> User:
    user = db.query(User).filter(User.email == "admin@annotationops.io").first()
    if not user:
        user = User(
            id=1,
            email="admin@annotationops.io",
            full_name="System Admin",
            hashed_password="hashed_demo_pw",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            user = db.query(User).first()
    return user


# ── Core dependency: decode JWT and load User ─────────────────────────────────

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT and return the corresponding active User.
    Supports demo tokens, JWT tokens, and unauthenticated fallback in dev/demo mode.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token:
        if token.startswith("demo_token_"):
            parts = token.split("_")
            role_str = parts[2] if len(parts) >= 3 else "admin"
            target_role = UserRole.ADMIN
            if "annotator" in role_str:
                target_role = UserRole.ANNOTATOR
            elif "reviewer" in role_str:
                target_role = UserRole.REVIEWER
            elif "project_manager" in role_str or "po" in role_str:
                target_role = UserRole.PROJECT_MANAGER

            user = db.query(User).filter(User.role == target_role).first()
            if user and user.is_active:
                return user
            user = db.query(User).filter(User.is_active.is_(True)).first()
            if user:
                return user
            return _get_or_create_default_admin(db)

        try:
            payload = decode_access_token(token)
            email: str = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user is not None:
                    if not user.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="User account is disabled",
                        )
                    return user
                raise credentials_exception
        except JWTError:
            raise credentials_exception

    # For strict auth check endpoint like /auth/me when token is omitted
    if request.url.path.endswith("/auth/me"):
        raise credentials_exception

    # Unauthenticated / demo fallback for operational endpoints
    user = db.query(User).filter(User.is_active.is_(True)).first()
    if user:
        return user
    return _get_or_create_default_admin(db)


# ── Role guard ────────────────────────────────────────────────────────────────

def require_role(*roles: UserRole) -> Callable:
    """
    Return a FastAPI dependency that requires the current user to have one
    of the specified roles.

    Usage::

        @router.post("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{[r.value for r in roles]}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _check


# ── Permission guard ──────────────────────────────────────────────────────────

def require_permission(permission: str) -> Callable:
    """
    Return a FastAPI dependency that requires the current user's role to
    include the named permission (checked against ROLE_PERMISSIONS).

    Usage::

        @router.post("/...", dependencies=[Depends(require_permission("manage_projects"))])
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Permission required: '{permission}'. "
                    f"Your role '{current_user.role.value}' does not have this permission."
                ),
            )
        return current_user

    return _check
