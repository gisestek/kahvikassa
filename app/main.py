from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import AsyncSessionLocal
from app.routers import (
    admin_analytics,
    admin_audit,
    admin_categories,
    admin_inventory,
    admin_products,
    admin_recipes,
    admin_settings,
    admin_themes,
    admin_users,
    admin_version,
    auth,
    kiosk,
    pages,
    supply,
)
from app.services.theme_service import ensure_active_theme_file_matches_settings

app = FastAPI(title="Kahvikassa")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(kiosk.router)
app.include_router(supply.router)
app.include_router(admin_users.router)
app.include_router(admin_categories.router)
app.include_router(admin_products.router)
app.include_router(admin_recipes.router)
app.include_router(admin_inventory.router)
app.include_router(admin_audit.router)
app.include_router(admin_analytics.router)
app.include_router(admin_settings.router)
app.include_router(admin_version.router)
app.include_router(admin_themes.router)


@app.on_event("startup")
async def regenerate_active_theme_file() -> None:
    """active-theme.css is gitignored generated state, not source — a fresh
    git clone (e.g. right after deploy.sh) won't have it. Regenerate it from
    the DB-stored selection on every boot so the right theme is always served."""
    async with AsyncSessionLocal() as db:
        await ensure_active_theme_file_matches_settings(db)
