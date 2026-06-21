import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models.user import User
from app.services.auth_service import list_active_users

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Cache-busts every /static/... reference (?v=...) on each process start, so a
# fresh deploy is never served from a browser's stale cached JS/CSS without a
# hard refresh — a real bug we hit once already.
templates.env.globals["static_version"] = str(int(time.time()))


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: AsyncSession = Depends(get_db_session)):
    users = await list_active_users(db)
    return templates.TemplateResponse(request, "index.html", {"users": users})


@router.get("/info.html", response_class=HTMLResponse)
async def info_page(request: Request):
    return templates.TemplateResponse(request, "info.html", {})


@router.get("/kioski", response_class=HTMLResponse)
async def kiosk_page(
    request: Request, current_user: User | None = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "kiosk.html", {"current_user": current_user})


@router.get("/toin-tavaraa", response_class=HTMLResponse)
async def supply_page(
    request: Request, current_user: User | None = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "supply.html", {"current_user": current_user})


@router.get("/vaihda-pin", response_class=HTMLResponse)
async def change_pin_page(
    request: Request, current_user: User | None = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "change_pin.html", {"current_user": current_user})


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request, current_user: User | None = Depends(get_current_user)
):
    if current_user is None or not current_user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "admin/dashboard.html", {"current_user": current_user})


def _admin_subpage(template_name: str):
    async def handler(request: Request, current_user: User | None = Depends(get_current_user)):
        if current_user is None or not current_user.is_admin:
            return RedirectResponse(url="/")
        return templates.TemplateResponse(request, template_name, {"current_user": current_user})

    return handler


router.add_api_route("/admin/kayttajat", _admin_subpage("admin/users.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/tuoteryhmat", _admin_subpage("admin/categories.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/myyntituotteet", _admin_subpage("admin/products.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/reseptit", _admin_subpage("admin/recipes.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/varasto", _admin_subpage("admin/inventory.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/tapahtumaloki", _admin_subpage("admin/audit.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/tilastot", _admin_subpage("admin/analytics.html"), methods=["GET"], response_class=HTMLResponse)
router.add_api_route("/admin/asetukset", _admin_subpage("admin/settings.html"), methods=["GET"], response_class=HTMLResponse)
