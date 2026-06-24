from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from flashcards_common import health_router, setup_logging, setup_otel
from generation_svc.config import get_settings
from generation_svc.routes import router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(_settings.log_level)
    setup_otel(app, _settings.service_name, _settings.otel_endpoint)
    yield


app = FastAPI(title="generation-svc", lifespan=lifespan)
app.include_router(health_router)
app.include_router(router)
