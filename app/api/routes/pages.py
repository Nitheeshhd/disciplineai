from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_read_session, get_write_session
from app.models.message import Message
from app.models.payment import Payment
from app.models.session import Session
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.dashboard import LiveStatsResponse
from app.schemas.task_tracking import FocusSessionSyncRequest, TaskStatusToggleRequest, UserProfileUpdateRequest
from app.services.task_tracking_service import TaskTrackingService

# Setup logger
logger = logging.getLogger(__name__)
FOCUS_TOTALS_SESSION_KEY = "disciplineai_focus_minutes"
MAX_FOCUS_TOTAL_DAYS = 31

# Template directory configuration
BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["UI Pages"])

def _render_page(request: Request, template: str, active_page: str, title: str) -> HTMLResponse:
    """Helper to render template responses with standard navigation context."""
    return templates.TemplateResponse(
        name=template,
        context={
            "request": request,
            "active_page": active_page,
            "page_title": title,
        }
    )


def _session_user_or_401(request: Request) -> dict:
    user = request.session.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _focus_totals(request: Request) -> dict[str, int]:
    raw = request.session.get(FOCUS_TOTALS_SESSION_KEY, {})
    if not isinstance(raw, dict):
        return {}

    payload: dict[str, int] = {}
    for day_key, minutes in raw.items():
        try:
            payload[str(day_key)] = max(int(minutes), 0)
        except (TypeError, ValueError):
            continue
    return payload


def _store_focus_totals(request: Request, totals: dict[str, int]) -> None:
    trimmed = dict(sorted(totals.items())[-MAX_FOCUS_TOTAL_DAYS:])
    request.session[FOCUS_TOTALS_SESSION_KEY] = trimmed


def _focus_minutes_for_day(request: Request, target_day: date) -> int:
    return int(_focus_totals(request).get(target_day.isoformat(), 0))


def _append_focus_minutes(request: Request, target_day: date, minutes: int) -> None:
    totals = _focus_totals(request)
    key = target_day.isoformat()
    totals[key] = max(int(totals.get(key, 0)) + max(int(minutes), 0), 0)
    _store_focus_totals(request, totals)

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> HTMLResponse:
    """SaaS Landing Page."""
    if request.session.get("user"):
        return RedirectResponse(url="/dashboard")
    
    return templates.TemplateResponse(
        name="landing.html",
        context={"request": request, "page_title": "Welcome"}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    db: AsyncSession = Depends(get_read_session)
) -> HTMLResponse:
    """Protected Dashboard Home."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)

    try:
        today_dt = datetime.now(timezone.utc)
        today_date = today_dt.date()
        week_ago_dt = today_dt - timedelta(days=6)
        week_ago_date = week_ago_dt.date()

        # 1. Fetch Summary Metrics
        total_users = (await db.execute(select(func.count(User.id)).where(User.is_deleted == False))).scalar() or 0
        sessions_today = (await db.execute(select(func.count(Session.id)).where(
            Session.created_at >= (today_dt - timedelta(days=1)),
            Session.is_deleted == False
        ))).scalar() or 0
        messages_today = (await db.execute(select(func.count(Message.id)).where(
            Message.message_date == today_date,
            Message.is_deleted == False
        ))).scalar() or 0
        revenue_today = (await db.execute(select(func.sum(Payment.amount)).where(
            Payment.paid_date == today_date,
            Payment.payment_status == "paid",
            Payment.is_deleted == False
        ))).scalar() or 0.0

        # ... (rest of the logic remains the same) ...
        # (Snippet truncated for brevity, but I will include the full updated function in the actual tool call)
        # Fetch 7-Day Time Series Data
        users_stmt = (
            select(func.date(User.created_at).label("day"), func.count(User.id))
            .where(User.created_at >= week_ago_dt, User.is_deleted == False)
            .group_by(func.date(User.created_at))
        )
        users_result = {str(r[0]): int(r[1]) for r in (await db.execute(users_stmt)).all()}

        messages_stmt = (
            select(Message.message_date.label("day"), func.count(Message.id))
            .where(Message.message_date >= week_ago_date, Message.is_deleted == False)
            .group_by(Message.message_date)
        )
        messages_result = {str(r[0]): int(r[1]) for r in (await db.execute(messages_stmt)).all()}

        dates_list, daily_users, daily_messages = [], [], []
        for i in range(7):
            curr_date = week_ago_date + timedelta(days=i)
            date_str = str(curr_date)
            dates_list.append(curr_date.strftime("%b %d"))
            daily_users.append(users_result.get(date_str, 0))
            daily_messages.append(messages_result.get(date_str, 0))

        recent_users = (await db.execute(select(User).where(User.is_deleted == False).order_by(User.created_at.desc()).limit(5))).scalars().all()
        recent_messages = (await db.execute(select(Message).where(Message.is_deleted == False).order_by(Message.created_at.desc()).limit(5))).scalars().all()

        return templates.TemplateResponse(
            name="summary.html",
            context={
                "request": request,
                "active_page": "summary",
                "page_title": "Analytics Dashboard",
                "user": user,
                "total_users": int(total_users),
                "sessions_today": int(sessions_today),
                "messages_today": int(messages_today),
                "revenue_today": float(revenue_today),
                "dates": dates_list,
                "daily_users": daily_users,
                "daily_messages": daily_messages,
                "recent_users": recent_users,
                "recent_messages": recent_messages,
            }
        )
    except Exception as e:
        logger.error(f"Dashboard render failed: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            name="summary.html",
            context={
                "request": request, "active_page": "summary", "page_title": "Analytics Dashboard", "user": user,
                "total_users": 0, "sessions_today": 0, "messages_today": 0, "revenue_today": 0.0,
                "dates": [], "daily_users": [], "daily_messages": [], "recent_users": [], "recent_messages": [],
            }
        )

@router.get("/summary", include_in_schema=False)
async def summary_redirect():
    return RedirectResponse(url="/dashboard")


@router.get("/api/live-stats", response_model=LiveStatsResponse)
async def live_stats(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
) -> LiveStatsResponse:
    user = _session_user_or_401(request)
    target_day = date.today()
    service = TaskTrackingService(session=db)
    stats = await service.build_live_stats(
        user_id=int(user["id"]),
        focus_time_today=_focus_minutes_for_day(request, target_day),
        target_day=target_day,
    )
    return LiveStatsResponse(**stats)


@router.post("/api/live-stats/focus", response_model=MessageResponse)
async def sync_focus_live_stats(
    request: Request,
    payload: FocusSessionSyncRequest,
) -> MessageResponse:
    _session_user_or_401(request)
    _append_focus_minutes(request, payload.focus_date or date.today(), payload.minutes)
    return MessageResponse(message="Focus session synced")


@router.get("/dashboard/tracker/state")
async def dashboard_tracker_state(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
) -> dict:
    user = _session_user_or_401(request)
    service = TaskTrackingService(session=db)
    return await service.build_state(user_id=int(user["id"]))


@router.post("/dashboard/tracker/toggle")
async def dashboard_tracker_toggle(
    request: Request,
    payload: TaskStatusToggleRequest,
    db: AsyncSession = Depends(get_write_session),
) -> dict:
    user = _session_user_or_401(request)
    service = TaskTrackingService(session=db)
    try:
        return await service.update_task_status(
            user_id=int(user["id"]),
            task_name=payload.task_name,
            status=payload.status,
            target_day=payload.task_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dashboard/profile/update")
async def dashboard_profile_update(
    request: Request,
    payload: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_write_session),
) -> dict:
    user = _session_user_or_401(request)
    if payload.name is None and payload.phone is None and payload.age is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")
    service = TaskTrackingService(session=db)
    try:
        state = await service.update_profile_settings(
            user_id=int(user["id"]),
            name=payload.name,
            phone=payload.phone,
            age=payload.age,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated_name = state.get("profile", {}).get("user_name")
    if updated_name:
        request.session["user"]["name"] = updated_name
    return state

def _auth_redirect(request: Request, template: str, active_page: str, title: str) -> HTMLResponse:
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        name=template,
        context={"request": request, "active_page": active_page, "page_title": title, "user": user}
    )

@router.get("/users", response_class=HTMLResponse)
async def users(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "users.html", "users", "Users")

@router.get("/bots", response_class=HTMLResponse)
async def bots(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "bots.html", "bots", "My Bots")

@router.get("/utm", response_class=HTMLResponse)
async def utm(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "utm.html", "utm", "UTM Generator")

@router.get("/website-extension", response_class=HTMLResponse)
async def website_extension(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "website_extension.html", "website_extension", "Website Extension")

@router.get("/errors", response_class=HTMLResponse)
async def errors(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "errors.html", "errors", "Bot Errors")

@router.get("/conversions", response_class=HTMLResponse)
async def conversions(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "conversions.html", "conversions", "Conversions")

@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "reports.html", "reports", "Reports")

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "profile.html", "profile", "Profile")

@router.get("/focus", response_class=HTMLResponse)
async def focus(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "focus.html", "focus", "Focus Timer")

@router.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "tasks.html", "tasks", "Tasks")

@router.get("/tasks/new", response_class=HTMLResponse)
async def new_task(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "new_task.html", "new_task", "New Task")

@router.get("/habits", response_class=HTMLResponse)
async def habits(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "habits.html", "habits", "Habits")

@router.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request) -> HTMLResponse:
    return _auth_redirect(request, "analytics.html", "analytics", "Analytics")
