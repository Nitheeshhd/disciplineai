from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_ui(request: Request) -> HTMLResponse:
    templates = getattr(request.app.state, "templates", None)
    if templates is None:
        templates = Jinja2Templates(directory="app/api/templates")
    settings = request.app.state.settings
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"app_name": settings.app_name},
    )
