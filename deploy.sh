#!/bin/bash
# One-button production deploy: pulls the latest commit from GitHub, rebuilds
# the web image, restarts the containers, and runs any pending Alembic
# migrations. Never touches the Postgres or signal-cli data volumes — only
# code and schema move, never data.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Haetaan uusin koodi GitHubista"
git fetch origin
git reset --hard origin/master

echo "$(git rev-parse --short HEAD)" > VERSION
echo "    Uusi versio: $(cat VERSION)"

echo "==> Rakennetaan web-kontti"
docker compose build web

echo "==> Käynnistetään kontit"
docker compose up -d

echo "==> Ajetaan tietokantamigraatiot (ei kosketa olemassa olevaa dataa)"
docker compose exec web alembic upgrade head

echo "==> Valmis. Käynnissä versio $(cat VERSION)."
