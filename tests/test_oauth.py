import os
import pytest
from httpx import AsyncClient, ASGITransport

# Configure provider envs for tests
os.environ.setdefault("WEIBO_CLIENT_ID", "testid")
os.environ.setdefault("WEIBO_CLIENT_SECRET", "testsecret")
os.environ.setdefault("WEIBO_REDIRECT_URI", "http://test/callback")

# Use SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_oauth.db")

from app.main import create_app  # noqa: E402
from app.api.v1.auth import oauth_service  # noqa: E402


class FakeKV:
    def __init__(self):
        self._store = {}

    async def set_json(self, key, value, ex=None):
        self._store[key] = value

    async def get_json(self, key):
        return self._store.get(key)

    async def delete(self, key):
        self._store.pop(key, None)


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class FakeClient:
    async def fetch_token(self, url, grant_type, code):
        # Simulate Weibo token response
        return {"access_token": "fake_token", "uid": "9001", "scope": ""}

    async def get(self, url, params):
        # Simulate user info
        return FakeResponse({"screen_name": "wb_user", "profile_image_url": "http://img"})

    def create_authorization_url(self, url, scope=None, state=None, params=None):
        return (f"{url}?state={state}", state)


@pytest.mark.asyncio
async def test_weibo_oauth_flow(monkeypatch):
    app = create_app()
    transport = ASGITransport(app=app)

    # Patch RedisKV and OAuth client
    oauth_service.redis = FakeKV()
    monkeypatch.setattr(oauth_service, "_client_for", lambda provider: FakeClient())

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1) Get authorize URL
        r = await ac.get("/api/v1/auth/oauth/weibo/authorize")
        assert r.status_code == 200
        data = r.json()
        assert "authorize_url" in data and "state" in data

        # 2) Callback
        r = await ac.get(
            "/api/v1/auth/oauth/weibo/callback",
            params={"code": "dummy-code", "state": data["state"]},
        )
        assert r.status_code == 200, r.text
        tokens = r.json()
        assert "access_token" in tokens and "refresh_token" in tokens


@pytest.mark.asyncio
async def test_unsupported_provider():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/auth/oauth/unknown/authorize")
        assert r.status_code == 400
