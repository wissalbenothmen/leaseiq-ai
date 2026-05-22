from __future__ import annotations
import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "StrongPass1!", "full_name": "New User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_weak_password_too_short(client):
    """Test that passwords shorter than 8 chars are rejected."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "Ab1!", "full_name": "Weak Pass"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(client):
    """Test that password without uppercase is rejected."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak2@example.com", "password": "alllower1!", "full_name": "No Upper"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_digit(client):
    """Test that password without digit is rejected."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak3@example.com", "password": "NoDigitPass!", "full_name": "No Digit"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test that registering with an existing email is rejected."""
    user_data = {"email": "dup@example.com", "password": "StrongPass1!", "full_name": "Dup User"}
    resp1 = await client.post("/api/v1/auth/register", json=user_data)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=user_data)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful login returns access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@example.com", "password": "StrongPass1!", "full_name": "Login User"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser@example.com", "password": "StrongPass1!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "badpass@example.com", "password": "StrongPass1!", "full_name": "Bad Pass"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "badpass@example.com", "password": "WrongPass1!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(auth_client):
    """Test /auth/me returns current user info."""
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    """Test /auth/me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
