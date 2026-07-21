from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def _cors_headers(request: Request) -> dict:
    # Responses built by handlers registered for bare Exception come from Starlette's
    # ServerErrorMiddleware, which sits outside CORSMiddleware — without these headers
    # the browser reports a CORS failure instead of surfacing the actual 500.
    origin = request.headers.get("origin")
    if origin and (origin in settings.cors_origins or "*" in settings.cors_origins):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return {}


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning("{path} {status} {detail}", path=request.url.path, status=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=_cors_headers(request),
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.error("{path} {exc}", path=request.url.path, exc=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=_cors_headers(request),
    )
