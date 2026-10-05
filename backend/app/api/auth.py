"""
Authentication API routes.

Endpoints:
  POST /auth/bootstrap  — create first Admin (only works once, while users table is empty)
  POST /auth/register   — Admin-only user registration
  POST /auth/login      — issue JWT token
  GET  /auth/me         — return current user's profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_role
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse


router = APIRouter(tags=["Auth"])


# ── Bootstrap ─────────────────────────────────────────────────────────────────

@router.post(
    "/bootstrap",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create the very first Admin account (one-shot — disabled once any user exists)",
)
def bootstrap_admin(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    One-shot endpoint that creates the initial Admin account.

    Returns HTTP 403 if **any** user already exists in the database,
    preventing privilege escalation.  After the first Admin exists, all
    further registrations must go through ``POST /auth/register`` (Admin JWT
    required).
    """
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Bootstrap is disabled — at least one user already exists. "
                "Use POST /auth/register with an Admin JWT to create new accounts."
            ),
        )

    # Force role to Admin regardless of what the caller sends
    user = User(
        email=payload.email.lower().strip(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ── Register (Admin only) ─────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user — Admin only",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new platform user.  Only Admins can call this endpoint.

    The ``role`` field in the request body sets the new user's role.
    """
    normalized_email = payload.email.lower().strip()

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{normalized_email}' already exists.",
        )

    user = User(
        email=normalized_email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT access token",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verify credentials and return a signed JWT.

    The token must be sent as ``Authorization: Bearer <token>`` on
    subsequent requests to protected endpoints.
    """
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled. Contact your administrator.",
        )

    token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return current authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
