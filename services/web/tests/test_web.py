"""Web BFF smoke tests — mocks all downstream service calls."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from web.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_page(client: AsyncClient) -> None:
    resp = await client.get("/login")
    assert resp.status_code == 200
    assert b"Log in" in resp.content


@pytest.mark.asyncio
async def test_register_page(client: AsyncClient) -> None:
    resp = await client.get("/register")
    assert resp.status_code == 200
    assert b"Create account" in resp.content


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_decks_redirects_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/decks", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_upload_redirects_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/upload", follow_redirects=False)
    assert resp.status_code == 302


@pytest.mark.asyncio
async def test_login_post_success(client: AsyncClient) -> None:
    with patch("web.clients.login", new_callable=AsyncMock, return_value="fake-token"):
        resp = await client.post(
            "/login", data={"email": "a@b.com", "password": "pass"}, follow_redirects=False
        )
    assert resp.status_code == 302
    assert "session" in resp.cookies


@pytest.mark.asyncio
async def test_login_post_failure(client: AsyncClient) -> None:
    import httpx

    with patch("web.clients.login", side_effect=httpx.HTTPStatusError("bad", request=None, response=None)):  # type: ignore[arg-type]
        resp = await client.post("/login", data={"email": "x@y.com", "password": "wrong"})
    assert resp.status_code == 200
    assert b"Invalid" in resp.content
