from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import (
    admin_analytics,
    admin_audit,
    admin_categories,
    admin_inventory,
    admin_products,
    admin_recipes,
    admin_settings,
    admin_users,
    admin_version,
    auth,
    kiosk,
    pages,
    supply,
)

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
