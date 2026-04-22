"""
SecureWealth Twin — Auth endpoint tests.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestRegister:

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email":     "newuser@test.in",
            "password":  "StrongPass123!",
            "full_name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token"  in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "dup@test.in", "password": "Pass12345!"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email":    "weak@test.in",
            "password": "short",
        })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email":    "not-an-email",
            "password": "ValidPass123!",
        })
        assert resp.status_code == 422


class TestLogin:

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "login@test.in", "password": "LoginPass123!"
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "login@test.in", "password": "LoginPass123!"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "wrongpw@test.in", "password": "CorrectPass123!"
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "wrongpw@test.in", "password": "WrongPassword!"
        })
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@test.in", "password": "AnyPass123!"
        })
        assert resp.status_code == 401


class TestProfile:

    async def test_get_me(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@securewealth.in"
        assert data["role"]  == "customer"

    async def test_update_me(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/api/v1/auth/me", headers=auth_headers, json={
            "full_name": "Updated Name",
            "phone":     "+919876543210",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"]     == "+919876543210"

    async def test_me_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403  # No Bearer token


class TestTokenRefresh:

    async def test_refresh_success(self, client: AsyncClient):
        reg = await client.post("/api/v1/auth/register", json={
            "email": "refresh@test.in", "password": "RefreshPass123!"
        })
        refresh_token = reg.json()["refresh_token"]
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        reg = await client.post("/api/v1/auth/register", json={
            "email": "badrefresh@test.in", "password": "BadRefresh123!"
        })
        access_token = reg.json()["access_token"]
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token  # Wrong token type
        })
        assert resp.status_code == 401
