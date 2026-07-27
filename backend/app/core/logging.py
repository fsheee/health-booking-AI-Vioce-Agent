import logging
import os
import sys
import time
from pathlib import Path

from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send


_IN_VERCEL = os.environ.get("VERCEL") == "1"


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()

        async def send_with_logging(message: dict) -> None:
            if message["type"] == "http.response.start":
                duration = time.time() - start
                logger.info(
                    "{} {} {} {:.2f}s",
                    scope.get("method", ""),
                    scope.get("path", ""),
                    message.get("status", 0),
                    duration,
                )
            await send(message)

        await self.app(scope, receive, send_with_logging)


def setup_logging():
    if _IN_VERCEL:
        _setup_vercel_logging()
    else:
        _setup_local_logging()

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def _setup_local_logging():
    log_path = Path("logs/app.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        rotation="10 MB",
        retention="1 month",
        level="INFO",
        format="{time} {level} {message}",
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="DEBUG" if __debug__ else "INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}",
    )


def _setup_vercel_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="{time:HH:mm:ss} | {level:<7} | {message}",
    )
