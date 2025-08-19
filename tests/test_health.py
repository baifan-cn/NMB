from httpx import AsyncClient
from httpx import ASGITransport

from app.main import app


async def test_healthcheck():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
