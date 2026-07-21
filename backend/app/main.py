import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler
from app.core.logging import LoggingMiddleware, setup_logging
from app.services.reminder_worker import start_scheduler, stop_scheduler

setup_logging()

# Patch socket to prefer IPv4 — this Windows machine has broken IPv6 routing,
# and httpcore (used by httpx, google-genai, assemblyai) tries IPv6 first,
# causing [Errno 11002] getaddrinfo failed.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_fallback_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except socket.gaierror:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_fallback_getaddrinfo


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_scheduler()
    yield
    await stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware execution order: last added = first executed.
# LoggingMiddleware must be added after CORSMiddleware so CORS runs first.
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.app_name}
