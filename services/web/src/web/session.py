"""Cookie-based session — stores the JWT so the browser never sees it."""
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from web.config import get_settings

_settings = get_settings()
_signer = URLSafeSerializer(_settings.session_secret, salt="session")

COOKIE_NAME = "session"


def set_session_token(response: Response, token: str) -> None:
    signed = _signer.dumps({"token": token})
    response.set_cookie(
        COOKIE_NAME,
        signed,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)


def get_token_from_request(request: Request) -> str | None:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        data = _signer.loads(raw)
        return str(data["token"])
    except (BadSignature, KeyError):
        return None


def require_token(request: Request) -> str:
    """Return the session token or raise a RedirectResponse exception to /login."""
    token = get_token_from_request(request)
    if not token:
        # Raise as an exception so FastAPI's exception handler can catch it
        raise _LoginRedirect()
    return token


class _LoginRedirect(Exception):
    """Raised when a route requires auth but no session token is present."""
    response = RedirectResponse("/login", status_code=302)
