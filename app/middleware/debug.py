import logging
import traceback
import sys
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DetailedDebugMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides detailed console feedback for errors during development.
    Prints full stack traces to the terminal even if global handlers are active.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            if settings.app_env.lower() == "development":
                # Print high-visibility error block to console
                print("\n" + "="*80)
                print(f"DEBUG EXCEPTION CAUGHT")
                print(f"Path: {request.method} {request.url.path}")
                print(f"Error: {exc}")
                print("-"*80)
                traceback.print_exc()
                print("="*80 + "\n")
            
            # Re-raise to let ErrorLoggingMiddleware or FastAPI handlers deal with the response
            raise exc
