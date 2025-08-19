import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure tests use local SQLite aiosqlite DB
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_auth.db")

from app.main import create_app  # noqa: E402


@pytest.mark.asyncio
async def test_register_login_profile_change_password_flow():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # register
        r = await ac.post("/api/v1/auth/register", json={
            "username": "tester",
            "email": "tester@example.com",
            "password": "StrongPassw0rd!"
        })
        assert r.status_code == 200, r.text
        user = r.json()
        assert user["username"] == "tester"

        # login
        r = await ac.post("/api/v1/auth/login", json={
            "username_or_email": "tester",
            "password": "StrongPassw0rd!"
        })
        assert r.status_code == 200, r.text
        tokens = r.json()
        assert "access_token" in tokens and "refresh_token" in tokens

        # profile
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        r = await ac.get("/api/v1/auth/profile", headers=headers)
        assert r.status_code == 200
        assert r.json()["username"] == "tester"

        # change password
        r = await ac.put("/api/v1/auth/change-password", headers=headers, json={
            "old_password": "StrongPassw0rd!",
            "new_password": "NewPassw0rd!"
        })
        assert r.status_code == 200

        # login with new password
        r = await ac.post("/api/v1/auth/login", json={
            "username_or_email": "tester",
            "password": "NewPassw0rd!"
        })
        assert r.status_code == 200
