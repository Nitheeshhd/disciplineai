from app.schemas.bots import BotCreateRequest, BotResponse, BotsListResponse
from app.schemas.analytics import AnalyticsTrendResponse, ProductivityMetricsResponse
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserMeResponse,
)
from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.dashboard import (
    ConversionRateResponse,
    DashboardDataResponse,
    DashboardSummary,
    DemographicBreakdown,
    ProductivityTrendResponse,
    RevenueTrendResponse,
)
from app.schemas.errors import ErrorLogItem, ErrorLogListResponse
from app.schemas.habit import HabitLogCreate, HabitLogResponse
from app.schemas.conversions import ConversionItem, ConversionListResponse, ConversionTrackingRateResponse
from app.schemas.reports import ReportItem, ReportListResponse
from app.schemas.task_tracking import TaskStatusToggleRequest, UserProfileUpdateRequest
from app.schemas.utm import CampaignGenerateRequest, CampaignListResponse, CampaignResponse
from app.schemas.users import UserDeleteResponse, UserListResponse, UserManagementItem

__all__ = [
    "AnalyticsTrendResponse",
    "BotCreateRequest",
    "BotResponse",
    "BotsListResponse",
    "CampaignGenerateRequest",
    "CampaignListResponse",
    "CampaignResponse",
    "ConversionItem",
    "ConversionListResponse",
    "ConversionRateResponse",
    "ConversionTrackingRateResponse",
    "DashboardDataResponse",
    "DashboardSummary",
    "DemographicBreakdown",
    "ErrorResponse",
    "ErrorLogItem",
    "ErrorLogListResponse",
    "HabitLogCreate",
    "HabitLogResponse",
    "LoginRequest",
    "MessageResponse",
    "ProductivityMetricsResponse",
    "ProductivityTrendResponse",
    "RefreshRequest",
    "RegisterRequest",
    "RevenueTrendResponse",
    "ReportItem",
    "ReportListResponse",
    "TaskStatusToggleRequest",
    "UserProfileUpdateRequest",
    "TokenPair",
    "UserDeleteResponse",
    "UserListResponse",
    "UserMeResponse",
    "UserManagementItem",
]
