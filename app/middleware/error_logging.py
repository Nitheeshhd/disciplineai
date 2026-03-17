from __future__ import annotations

import logging
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import WriteSessionLocal
from app.core.security import decode_access_token
from app.repositories.error_log_repository import ErrorLogRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    def _extract_user_id(self, request: Request) -> int | None:
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1].strip()
        if not token:
            return None
        try:
            payload = decode_access_token(token, settings)
            uid = payload.get("uid")
            return int(uid) if uid is not None else None
        except Exception:
            return None

    def _extract_command(self, request: Request) -> str:
        override = request.headers.get("x-command")
        if override and override.strip():
            return override.strip()[:255]
        return f"{request.method} {request.url.path}"[:255]

    async def dispatch(self, request: Request, call_next):
        trace_id = getattr(request.state, "request_id", "-")
        try:
            return await call_next(request)
        except Exception as exc:  # pragma: no cover - runtime path
            stack_trace = traceback.format_exc()
            logger.exception("Unhandled exception, trace_id=%s", trace_id)
            user_id = self._extract_user_id(request)
            command = self._extract_command(request)

            async with WriteSessionLocal() as session:
                repo = ErrorLogRepository(session)
                try:
                    await repo.create(
                        user_id=user_id,
                        command=command,
                        trace_id=trace_id,
                        path=request.url.path,
                        method=request.method,
                        status_code=500,
                        error_type=exc.__class__.__name__,
                        error_message=str(exc),
                        stack_trace=stack_trace,
                        metadata={
                            "query": str(request.query_params),
                            "headers": {
                                "user-agent": request.headers.get("user-agent"),
                                "x-forwarded-for": request.headers.get("x-forwarded-for"),
                            },
                        },
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception("Failed persisting error log, trace_id=%s", trace_id)

            error_content = {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                    "trace_id": trace_id,
                }
            }

            # In development, show the full error details for debugging
            if settings.app_env.lower() == "development":
                error_content["error"]["message"] = str(exc)
                error_content["error"]["details"] = {
                    "type": exc.__class__.__name__,
                    "stack_trace": stack_trace.splitlines()[-5:], # Last 5 lines for brevity
                }

            return JSONResponse(
                status_code=500,
                content=error_content,
            )
