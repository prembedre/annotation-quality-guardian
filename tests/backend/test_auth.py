"""
Tests for the auth endpoints:
  - bootstrap creates first Admin
  - bootstrap rejects when a user already exists
  - login succeeds with correct credentials
  - login rejects wrong password (401)
  - a role-restricted route returns 403 for an unauthorized role
  - GET /auth/me returns profile for a valid token
"""

import pytest
from fastapi.testclient import TestClient

# conftest.py already sets ENV=testing and wires up the SQLite in-memory DB


# ── Helpers ───────────────────────────────────────────────────────────────────

BOOTSTRAP_PAYLOAD = {
    "email": "admin@example.com",
    "full_name": "AQG Admin",
    "password": "Admin1234!",
    "role": "admin",
}

ANNOTATOR_PAYLOAD = {
    "email": "annotator@example.com",
    "full_name": "AQG Annotator",
    "password": "Annot1234!",
    "role": "annotator",
}


def _bootstrap(client: TestClient) -> dict:
    """Create the first Admin via /auth/bootstrap and return the token response."""
    resp = client.post("/auth/bootstrap", json=BOOTSTRAP_PAYLOAD)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _admin_token(client: TestClient) -> str:
    """Return Admin Bearer token string."""
    data = _bootstrap(client)
    return data["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBootstrap:
    def test_bootstrap_creates_admin(self, client: TestClient):
        """POST /auth/bootstrap succeeds when users table is empty and returns a token."""
        resp = client.post("/auth/bootstrap", json=BOOTSTRAP_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == BOOTSTRAP_PAYLOAD["email"]
        assert data["user"]["role"] == "admin"

    def test_bootstrap_rejects_when_user_exists(self, client: TestClient):
        """POST /auth/bootstrap returns 403 when at least one user already exists."""
        _bootstrap(client)  # Create first admin

        # Attempt a second bootstrap
        resp = client.post(
            "/auth/bootstrap",
            json={**BOOTSTRAP_PAYLOAD, "email": "second@example.com"},
        )
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()


class TestLogin:
    def test_login_success(self, client: TestClient):
        """POST /auth/login with correct credentials returns 200 and a token."""
        _bootstrap(client)
        resp = client.post(
            "/auth/login",
            json={"email": BOOTSTRAP_PAYLOAD["email"], "password": BOOTSTRAP_PAYLOAD["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"

    def test_login_wrong_password(self, client: TestClient):
        """POST /auth/login with the wrong password returns 401."""
        _bootstrap(client)
        resp = client.post(
            "/auth/login",
            json={"email": BOOTSTRAP_PAYLOAD["email"], "password": "WrongPassword99!"},
        )
        assert resp.status_code == 401
        assert "incorrect" in resp.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """POST /auth/login with an unknown email returns 401."""
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "anything"},
        )
        assert resp.status_code == 401


class TestGetMe:
    def test_get_me_with_valid_token(self, client: TestClient):
        """GET /auth/me returns the authenticated user's profile."""
        token = _admin_token(client)
        resp = client.get("/auth/me", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == BOOTSTRAP_PAYLOAD["email"]
        assert data["role"] == "admin"
        assert data["is_active"] is True

    def test_get_me_without_token_returns_401(self, client: TestClient):
        """GET /auth/me without a token returns 401."""
        resp = client.get("/auth/me")
        assert resp.status_code == 401


class TestRBACEnforcement:
    def test_role_restricted_route_rejects_annotator(self, client: TestClient):
        """
        An Annotator JWT should be rejected (403) when hitting an Admin-only
        endpoint (/auth/register requires Admin role).
        """
        # Bootstrap Admin, then register an Annotator
        admin_token = _admin_token(client)
        reg_resp = client.post(
            "/auth/register",
            json=ANNOTATOR_PAYLOAD,
            headers=_auth_headers(admin_token),
        )
        assert reg_resp.status_code == 201

        # Login as Annotator
        login_resp = client.post(
            "/auth/login",
            json={"email": ANNOTATOR_PAYLOAD["email"], "password": ANNOTATOR_PAYLOAD["password"]},
        )
        assert login_resp.status_code == 200
        annotator_token = login_resp.json()["access_token"]

        # Annotator tries to register a user — Admin-only endpoint → expect 403
        resp = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "NewUser1234!",
                "role": "reviewer",
            },
            headers=_auth_headers(annotator_token),
        )
        assert resp.status_code == 403
        assert "access denied" in resp.json()["detail"].lower()

    def test_admin_can_register_users(self, client: TestClient):
        """Admin JWT successfully registers a new user."""
        admin_token = _admin_token(client)
        resp = client.post(
            "/auth/register",
            json=ANNOTATOR_PAYLOAD,
            headers=_auth_headers(admin_token),
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "annotator"
