from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import pathlib

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from flashcards_common import health_router, setup_logging, setup_otel
from web.config import get_settings
from web.routes import router
from web.session import _LoginRedirect

_settings = get_settings()
_static_dir = pathlib.Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(_settings.log_level)
    setup_otel(app, _settings.service_name, _settings.otel_endpoint)
    yield


app = FastAPI(title="web", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
app.include_router(health_router)
app.include_router(router)


@app.exception_handler(_LoginRedirect)
async def login_redirect_handler(request: Request, exc: _LoginRedirect) -> RedirectResponse:
    return exc.response
