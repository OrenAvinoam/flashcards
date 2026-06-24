from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

health_router = APIRouter()

_readiness_checks: list[Callable[[], Coroutine[Any, Any, bool]]] = []


def register_readiness_check(fn: Callable[[], Coroutine[Any, Any, bool]]) -> None:
    _readiness_checks.append(fn)


@health_router.get("/healthz")
async def liveness() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@health_router.get("/readyz")
async def readiness() -> JSONResponse:
    results: dict[str, str] = {}
    all_ok = True
    for check in _readiness_checks:
        name = check.__name__
        try:
            ok = await check()
            results[name] = "ok" if ok else "fail"
            if not ok:
                all_ok = False
        except Exception:
            results[name] = "error"
            all_ok = False

    status_code = 200 if all_ok else 503
    return JSONResponse({"status": "ok" if all_ok else "degraded", "checks": results}, status_code=status_code)
