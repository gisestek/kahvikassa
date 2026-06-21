import re
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSettings
from app.models.user import User
from app.services.admin_service import APP_SETTINGS_ROW_ID, get_app_settings
from app.services.audit_service import log_system_change

_STATIC_CSS_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "css"
_THEMES_DIR = _STATIC_CSS_DIR / "themes"
_ACTIVE_THEME_PATH = _STATIC_CSS_DIR / "active-theme.css"

_NAME_PATTERN = re.compile(r"THEME_NAME:\s*(.+?)\s*\*/")

DEFAULT_THEME_SLUG = "gootti"


def list_available_themes() -> list[dict]:
    """Scans static/css/themes/ for *.css files — adding a new theme is just
    dropping a file there, no code change needed. Display name comes from a
    `/* THEME_NAME: ... */` header comment on the file's first line."""
    themes = []
    for path in sorted(_THEMES_DIR.glob("*.css")):
        slug = path.stem
        first_line = path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size else ""
        match = _NAME_PATTERN.search(first_line)
        themes.append({"slug": slug, "name": match.group(1) if match else slug})
    return themes


def _theme_file_path(slug: str) -> Path:
    candidate = (_THEMES_DIR / f"{slug}.css").resolve()
    if candidate.parent != _THEMES_DIR.resolve() or not candidate.is_file():
        raise ValueError("Tuntematon teema")
    return candidate


def write_active_theme_file(slug: str) -> None:
    content = _theme_file_path(slug).read_text(encoding="utf-8")
    _ACTIVE_THEME_PATH.write_text(content, encoding="utf-8")


async def ensure_active_theme_file_matches_settings(db: AsyncSession) -> None:
    """Regenerates active-theme.css from the DB-stored selection if it's
    missing — e.g. right after a fresh git clone, since the generated file
    is gitignored on purpose (it's derived state, not source)."""
    settings = await get_app_settings(db)
    slug = settings.active_theme or DEFAULT_THEME_SLUG
    try:
        write_active_theme_file(slug)
    except ValueError:
        write_active_theme_file(DEFAULT_THEME_SLUG)


async def activate_theme(db: AsyncSession, admin_user: User, slug: str) -> str:
    available_slugs = {t["slug"] for t in list_available_themes()}
    if slug not in available_slugs:
        raise ValueError("Tuntematon teema")

    write_active_theme_file(slug)

    settings = await db.get(AppSettings, APP_SETTINGS_ROW_ID)
    settings.active_theme = slug
    await log_system_change(db, admin_user, f"Teema vaihdettu: {slug}", {"entity": "theme", "action": "update"})
    await db.commit()
    return slug
