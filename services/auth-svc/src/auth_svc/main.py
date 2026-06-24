from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from auth_svc.config import get_settings
from auth_svc.routes import router
from flashcards_common import health_router, setup_logging, setup_otel

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(_settings.log_level)
    setup_otel(app, _settings.service_name, _settings.otel_endpoint)
    yield


app = FastAPI(title="auth-svc", lifespan=lifespan)
app.include_router(health_router)
app.include_router(router)
