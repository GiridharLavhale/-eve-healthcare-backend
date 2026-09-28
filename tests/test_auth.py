"""Authentication API tests."""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


def test_signup_success(client: TestClient):
    """Verifies that a valid user registration succeeds and returns clean user info without password."""
    payload = {
        "email": "alice@example.com",
        "password": "SecurePassword123!",
        "full_name": "Alice Wonderland",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Wonderland"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_signup_duplicate_email(client: TestClient):
    """Verifies that registering with an existing email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    res1 = client.post("/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/auth/signup", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_signup_normalizes_email_case(client: TestClient):
    """Verifies that email is normalized to lowercase on signup and duplicate check is case-insensitive."""
    payload1 = {
        "email": "MixedCase@Example.COM",
        "password": "Password123!",
        "full_name": "Mixed Case",
    }
    res1 = client.post("/auth/signup", json=payload1)
    assert res1.status_code == 201
    assert res1.json()["email"] == "mixedcase@example.com"

    payload2 = {
        "email": "mixedcase@example.com",
        "password": "Password123!",
        "full_name": "Another User",
    }
    res2 = client.post("/auth/signup", json=payload2)
    assert res2.status_code == 409


def test_signup_invalid_email(client: TestClient):
    """Verifies that invalid email formats are rejected with 422."""
    payload = {
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Bad Email",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 422


def test_signup_short_password(client: TestClient):
    """Verifies that passwords shorter than 8 characters are rejected."""
    payload = {
        "email": "shortpass@example.com",
        "password": "123",
        "full_name": "Short Pass",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 422


def test_login_success(client: TestClient):
    """Verifies that valid credentials return a JWT access token."""
    # Signup first
    client.post(
        "/auth/signup",
        json={
            "email": "login_user@example.com",
            "password": "ValidPassword123!",
            "full_name": "Login User",
        },
    )

    # Login
    response = client.post(
        "/auth/login",
        json={"email": "login_user@example.com", "password": "ValidPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_wrong_password(client: TestClient):
    """Verifies that incorrect password returns 401 Unauthorized."""
    client.post(
        "/auth/signup",
        json={
            "email": "wrong_pass@example.com",
            "password": "RealPassword123!",
            "full_name": "Wrong Pass User",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "wrong_pass@example.com", "password": "IncorrectPassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_email(client: TestClient):
    """Verifies that non-existent email returns 401 Unauthorized."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


def test_unauthenticated_access_to_protected_route(client: TestClient):
    """Verifies that calling a protected endpoint without JWT returns 401."""
    response = client.get("/bookings/")
    assert response.status_code == 401


def test_invalid_jwt_token(client: TestClient):
    """Verifies that providing a malformed or forged JWT returns 401."""
    response = client.get(
        "/bookings/",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_expired_jwt_token(client: TestClient, test_user):
    """Verifies that an expired JWT token returns 401."""
    expired_token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    response = client.get(
        "/bookings/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
