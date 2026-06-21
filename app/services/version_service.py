import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# Written by deploy.sh right before `docker compose build`, from the commit
# that's actually being deployed — not generated inside the container, since
# the .git history isn't reliably present in the image.
_VERSION_FILE = Path(__file__).resolve().parent.parent.parent / "VERSION"

_GITHUB_REPO = "gisestek/kahvikassa"
_GITHUB_BRANCH = "master"


def get_current_version() -> str:
    try:
        return _VERSION_FILE.read_text().strip() or "dev"
    except FileNotFoundError:
        return "dev"


async def get_latest_remote_commit() -> str | None:
    """Best-effort lookup of the newest commit on GitHub. Returns None on any
    failure (no network, rate limited, repo renamed, etc.) — checking for
    updates must never break the admin dashboard."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{_GITHUB_REPO}/commits/{_GITHUB_BRANCH}",
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            return response.json()["sha"][:7]
    except (httpx.HTTPError, KeyError, ValueError):
        logger.info("Could not check for a newer Kahvikassa version", exc_info=True)
        return None
