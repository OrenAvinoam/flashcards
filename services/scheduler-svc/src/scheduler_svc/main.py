from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response

from scheduler_svc.config import get_settings
from scheduler_svc.routes import router
from scheduler_svc.token_context import current_token
from flashcards_common import health_router, setup_logging, setup_otel

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(_settings.log_level)
    setup_otel(app, _settings.service_name, _settings.otel_endpoint)
    yield


app = FastAPI(title="scheduler-svc", lifespan=lifespan)
app.include_router(health_router)
app.include_router(router)


@app.middleware("http")
async def extract_token(request: Request, call_next: "Callable") -> Response:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ")
        token_ctx = current_token.set(token)
        try:
            return await call_next(request)
        finally:
            current_token.reset(token_ctx)
    return await call_next(request)


from collections.abc import Callable  # noqa: E402
