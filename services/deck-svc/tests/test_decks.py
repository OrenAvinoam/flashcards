import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_deck(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post("/decks", json={"name": "My Deck"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "My Deck"


@pytest.mark.asyncio
async def test_list_decks(client: AsyncClient, auth_headers: dict) -> None:
    await client.post("/decks", json={"name": "Deck A"}, headers=auth_headers)
    await client.post("/decks", json={"name": "Deck B"}, headers=auth_headers)
    resp = await client.get("/decks", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_create_card(client: AsyncClient, auth_headers: dict) -> None:
    deck = (await client.post("/decks", json={"name": "D"}, headers=auth_headers)).json()
    resp = await client.post(
        f"/decks/{deck['id']}/cards",
        json={"front": "Q", "back": "A"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["front"] == "Q"


@pytest.mark.asyncio
async def test_update_card_fsrs(client: AsyncClient, auth_headers: dict) -> None:
    deck = (await client.post("/decks", json={"name": "D"}, headers=auth_headers)).json()
    card = (
        await client.post(
            f"/decks/{deck['id']}/cards", json={"front": "Q", "back": "A"}, headers=auth_headers
        )
    ).json()
    new_state = {"stability": 2.5, "difficulty": 4.0, "due_at": "2099-01-01T00:00:00Z"}
    resp = await client.patch(
        f"/cards/{card['id']}", json={"fsrs_state": new_state}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["fsrs_state"]["stability"] == 2.5


@pytest.mark.asyncio
async def test_delete_deck(client: AsyncClient, auth_headers: dict) -> None:
    deck = (await client.post("/decks", json={"name": "ToDelete"}, headers=auth_headers)).json()
    resp = await client.delete(f"/decks/{deck['id']}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
