"""Integration tests for authentication, password updates, and admin user management."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_login_and_me(async_client: AsyncClient):
    """Verify login issues a JWT and /auth/me returns user profile."""
    # Seeded admin login
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@company.com", "password": "admin@123"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@company.com"
    assert data["user"]["role"] == "admin"

    token = data["access_token"]
    # Access protected /auth/me
    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "admin@company.com"


@pytest.mark.asyncio
async def test_admin_create_and_list_users(async_client: AsyncClient):
    """Verify admin can register new users and list them."""
    # Login as admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@company.com", "password": "admin@123"},
    )
    token = login_resp.json()["access_token"]

    # Register a new creator user
    create_resp = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "designer@company.com",
            "password": "designer@123",
            "role": "member",
            "brand_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["email"] == "designer@company.com"

    # Verify newly created user can log in
    designer_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "designer@company.com", "password": "designer@123"},
    )
    assert designer_login.status_code == 200
    assert designer_login.json()["user"]["role"] == "member"

    # List all users
    list_resp = await async_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    emails = [u["email"] for u in list_resp.json()]
    assert "designer@company.com" in emails


@pytest.mark.asyncio
async def test_change_password(async_client: AsyncClient):
    """Verify authenticated user can update their password."""
    # Login
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "creator@company.com", "password": "creator@123"},
    )
    token = login_resp.json()["access_token"]

    # Change password
    change_resp = await async_client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "creator@123", "new_password": "new_secret_password_123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change_resp.status_code == 200

    # Old password fails
    fail_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "creator@company.com", "password": "creator@123"},
    )
    assert fail_login.status_code == 401

    # New password succeeds
    success_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "creator@company.com", "password": "new_secret_password_123"},
    )
    assert success_login.status_code == 200
