# Kahvikassa

Self-hosted, luottamukseen perustuva kioski-POS-järjestelmä työpaikan kahvikassalle.
Käyttäjä valitsee nimensä, syöttää PIN-koodin, ja ostaa tuotteita muutamassa
sekunnissa — ei verkkokauppaa, ei maksukortteja, vain yksinkertainen kioski jossa
saldo, varasto ja resepteistä laskettu kulutus pysyvät ajan tasalla.

Tekninen toteutus: FastAPI + PostgreSQL, Jinja2 + vanilla JS, Docker Compose.
Valinnainen Signal-integraatio ilmoittaa varaston loppumisesta ja kuukausimaksun
veloituksesta.

## Pikastartti

```
cp .env.example .env   # aseta SECRET_KEY
docker compose up -d --build
docker compose exec web alembic upgrade head
```

Avaa `http://palvelimen-osoite:8000/`.

## Dokumentaatio

Tarkemmat kuvaukset löytyvät `docs/`-kansiosta:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — kerrosarkkitehtuuri ja keskeiset suunnitteluratkaisut
- [DATABASE.md](docs/DATABASE.md) — tietokannan rakenne
- [API.md](docs/API.md) — rajapinnat
- [INSTALL.md](docs/INSTALL.md) — asennus ja Signal-integraation käyttöönotto
- [USER_WORKFLOWS.md](docs/USER_WORKFLOWS.md) — käyttäjän ja ylläpitäjän työnkulut

