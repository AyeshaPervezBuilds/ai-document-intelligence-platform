"""Tests for authentication endpoints."""
import uuid


def _unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_user(client):
    email = _unique_email()
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "hashed_password" not in data  # never leak password


def test_register_duplicate_email_fails(client):
    email = _unique_email()
    payload = {"email": email, "password": "StrongPass123!"}
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400


def test_register_weak_password_fails(client):
    response = client.post(
        "/auth/register",
        json={"email": _unique_email(), "password": "weak"},
    )
    assert response.status_code == 422


def test_login_success(client):
    email = _unique_email()
    password = "StrongPass123!"
    client.post("/auth/register", json={"email": email, "password": password})

    response = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    email = _unique_email()
    client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPass123!"},
    )

    response = client.post(
        "/auth/login", json={"email": email, "password": "WrongPass999!"}
    )
    assert response.status_code == 401


def test_get_me_with_token(client):
    email = _unique_email()
    password = "StrongPass123!"
    client.post("/auth/register", json={"email": email, "password": password})

    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_get_me_without_token_fails(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)