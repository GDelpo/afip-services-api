"""Admin dashboard — minimal login + home page. Stack: Jinja2 + Tailwind browser build."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["DASHBOARD"])

# Expose static files (self-hosted Tailwind / Lucide in future iterations)
static_app = StaticFiles(directory=str(BASE_DIR / "static"))


def mount_static(app):  # pragma: no cover
    """Caller can optionally mount static files at /dashboard/static."""
    app.mount("/dashboard/static", static_app, name="dashboard_static")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "api_prefix": settings.api_prefix,
        },
    )


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "api_prefix": settings.api_prefix,
            "active_page": "home",
        },
    )
