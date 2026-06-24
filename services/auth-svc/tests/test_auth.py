import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient) -> None:
    resp = await client.post("/register", json={"email": "test@example.com", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "secret123"}
    await client.post("/register", json=payload)
    resp = await client.post("/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient) -> None:
    await client.post("/register", json={"email": "login@example.com", "password": "mypassword"})
    resp = await client.post("/login", json={"email": "login@example.com", "password": "mypassword"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post("/register", json={"email": "wp@example.com", "password": "correct"})
    resp = await client.post("/login", json={"email": "wp@example.com", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient) -> None:
    await client.post("/register", json={"email": "me@example.com", "password": "pass123"})
    login = await client.post("/login", json={"email": "me@example.com", "password": "pass123"})
    token = login.json()["access_token"]

    resp = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/me")
    assert resp.status_code == 403
