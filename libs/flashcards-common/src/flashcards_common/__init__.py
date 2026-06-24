from flashcards_common.health import health_router
from flashcards_common.http import make_http_client
from flashcards_common.jwt import JWTUser, jwt_dependency
from flashcards_common.logging import setup_logging
from flashcards_common.otel import setup_otel
from flashcards_common.settings import CommonSettings

__all__ = [
    "CommonSettings",
    "setup_logging",
    "setup_otel",
    "health_router",
    "jwt_dependency",
    "JWTUser",
    "make_http_client",
]
