from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware
from app.analytics import register_analytics_event_handlers
from app.api.routes import analytics, auth, auth_oauth, bots, conversions, dashboard, errors, habits, health, metrics, pages, reports, telegram, users, utm, test_error
from app.core.config import get_settings
from app.core.database import WriteSessionLocal, init_models
from app.core.exceptions import ApplicationError, application_error_handler
from app.core.logging import configure_logging
from app.core.openapi import build_custom_openapi
from app.middleware import (
    DetailedDebugMiddleware,
    ErrorLoggingMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
)
from app.services.bootstrap_service import BootstrapService
from app.workers.scheduler import build_scheduler

settings = get_settings()
configure_logging(settings.log_level, settings.app_env)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    register_analytics_event_handlers()

    async with WriteSessionLocal() as session:
        bootstrap = BootstrapService(session=session, settings=settings)
        await bootstrap.seed_roles_and_admin()

    scheduler = None
    if settings.scheduler_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
        logger.info("APScheduler started")

    app.state.scheduler = scheduler
    app.state.settings = settings
    app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)
app.openapi = build_custom_openapi(app)
app.state.settings = settings
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(RequestIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(DetailedDebugMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="session",
    same_site="none",
    https_only=True,
    max_age=60 * 60 * 24 * 7,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "api" / "static")), name="static")

app.include_router(auth_oauth.router)
app.include_router(pages.router)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(metrics.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(conversions.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(bots.router, prefix=settings.api_prefix)
app.include_router(errors.router, prefix=settings.api_prefix)
app.include_router(utm.router, prefix=settings.api_prefix)
app.include_router(habits.router, prefix=settings.api_prefix)
app.include_router(telegram.router)
app.include_router(test_error.router, prefix=settings.api_prefix)


@app.exception_handler(ApplicationError)
async def handle_application_error(request: Request, exc: ApplicationError):
    return await application_error_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Invalid request payload",
                "details": exc.errors(),
                "trace_id": getattr(request.state, "request_id", None),
            }
        },
    )
