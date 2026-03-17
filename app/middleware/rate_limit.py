from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.redis import redis_client

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{request.url.path}"

        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, settings.rate_limit_window_seconds)
        except Exception:
            # Fail-open if Redis is unavailable to protect platform availability.
            return await call_next(request)

        if current > settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Retry later.",
                    }
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(settings.rate_limit_requests - current, 0))
        return response
