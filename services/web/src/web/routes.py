from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Form, Request, Response, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web import clients
from web.session import clear_session, get_token_from_request, require_token, set_session_token

import pathlib

_templates_dir = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

router = APIRouter()


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> HTMLResponse:
    context: dict[str, Any] = {"request": request, **(ctx or {})}
    return templates.TemplateResponse(template, context)


# --- Auth ---

@router.get("/login")
async def login_page(request: Request) -> HTMLResponse:
    return _render(request, "login.html")


@router.post("/login")
async def do_login(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    try:
        token = await clients.login(email, password)
    except httpx.HTTPStatusError:
        return _render(request, "login.html", {"error": "Invalid email or password"})

    resp = RedirectResponse("/decks", status_code=status.HTTP_302_FOUND)
    set_session_token(resp, token)
    return resp


@router.get("/register")
async def register_page(request: Request) -> HTMLResponse:
    return _render(request, "register.html")


@router.post("/register")
async def do_register(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    try:
        await clients.register(email, password)
    except httpx.HTTPStatusError as e:
        msg = "Email already registered" if e.response.status_code == 409 else "Registration failed"
        return _render(request, "register.html", {"error": msg})
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout() -> Response:
    resp = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    clear_session(resp)
    return resp


# --- Decks ---

@router.get("/decks")
async def decks_page(request: Request) -> Response:
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    try:
        decks = await clients.list_decks(token)
    except httpx.HTTPStatusError:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return _render(request, "decks.html", {"decks": decks})


@router.post("/decks")
async def create_deck(
    request: Request,
    name: Annotated[str, Form()],
) -> Response:
    token = require_token(request)
    await clients.create_deck(token, name)
    return RedirectResponse("/decks", status_code=status.HTTP_302_FOUND)


@router.get("/decks/{deck_id}")
async def deck_detail(request: Request, deck_id: str) -> Response:
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    deck = await clients.get_deck(token, deck_id)
    cards = await clients.list_cards(token, deck_id)
    return _render(request, "deck_detail.html", {"deck": deck, "cards": cards})


@router.post("/decks/{deck_id}/cards")
async def add_card(
    request: Request,
    deck_id: str,
    front: Annotated[str, Form()],
    back: Annotated[str, Form()],
) -> Response:
    token = require_token(request)
    await clients.create_card(token, deck_id, front, back)
    return RedirectResponse(f"/decks/{deck_id}", status_code=status.HTTP_302_FOUND)


@router.post("/cards/{card_id}/delete")
async def delete_card(request: Request, card_id: str) -> Response:
    token = require_token(request)
    card_info = request.query_params.get("deck_id", "")
    await clients.delete_card(token, card_id)
    if card_info:
        return RedirectResponse(f"/decks/{card_info}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse("/decks", status_code=status.HTTP_302_FOUND)


# --- Study ---

@router.get("/decks/{deck_id}/study")
async def study_page(request: Request, deck_id: str) -> Response:
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    deck = await clients.get_deck(token, deck_id)
    due_cards = await clients.get_due_cards(token, limit=1)
    # Filter to this deck
    deck_due = [c for c in due_cards if c.get("deck_id") == deck_id]
    card = deck_due[0] if deck_due else None
    return _render(request, "study.html", {"deck": deck, "card": card})


@router.post("/study/review")
async def submit_review(
    request: Request,
    card_id: Annotated[str, Form()],
    deck_id: Annotated[str, Form()],
    grade: Annotated[str, Form()],
) -> Response:
    token = require_token(request)
    await clients.review_card(token, card_id, grade)
    return RedirectResponse(f"/decks/{deck_id}/study", status_code=status.HTTP_302_FOUND)


# --- Upload / Generation ---

@router.get("/upload")
async def upload_page(request: Request) -> Response:
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    decks = await clients.list_decks(token)
    return _render(request, "upload.html", {"decks": decks})


@router.post("/upload")
async def do_upload(
    request: Request,
    text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    count: Annotated[int, Form()] = 10,
) -> Response:
    token = require_token(request)
    if file and file.filename:
        raw = await file.read()
        job_id = await clients.enqueue_generation_pdf(token, raw, file.filename, count)
    elif text:
        job_id = await clients.enqueue_generation(token, text, count)
    else:
        decks = await clients.list_decks(token)
        return _render(request, "upload.html", {"error": "Provide text or a file.", "decks": decks})

    return RedirectResponse(f"/jobs/{job_id}", status_code=status.HTTP_302_FOUND)


@router.get("/jobs/{job_id}")
async def job_status_page(request: Request, job_id: str) -> Response:
    token = get_token_from_request(request)
    if not token:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    job = await clients.get_job_status(token, job_id)
    decks = await clients.list_decks(token)
    return _render(request, "job_status.html", {"job": job, "job_id": job_id, "decks": decks})


@router.post("/jobs/{job_id}/add-to-deck")
async def add_cards_to_deck(
    request: Request,
    job_id: str,
    deck_id: Annotated[str, Form()],
    fronts: Annotated[list[str], Form()],
    backs: Annotated[list[str], Form()],
) -> Response:
    token = require_token(request)
    for front, back in zip(fronts, backs):
        await clients.create_card(token, deck_id, front, back)
    return RedirectResponse(f"/decks/{deck_id}", status_code=status.HTTP_302_FOUND)


# --- Root ---

@router.get("/")
async def root(request: Request) -> Response:
    return RedirectResponse("/decks", status_code=status.HTTP_302_FOUND)
