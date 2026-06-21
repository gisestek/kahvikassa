# Arkkitehtuuri

## Yleiskuva

Kahvikassa on self-hosted, luottamukseen perustuva kioski-POS-järjestelmä työpaikan
kahvikassaa varten. Se ei ole verkkokauppa-alusta: ei ostoskoria joka säilyy istuntojen
välillä, ei maksukortteja, ei tilausvahvistuksia sähköpostiin. Tavoite on, että koko
ostotapahtuma (nimi → PIN → tuote → OK) kestää muutaman sekunnin.

## Kerrosarkkitehtuuri

```
templates/ + static/        Jinja2 + vanilla JS -kioskikäyttöliittymä
        |
app/routers/                FastAPI-reitit: HTTP-rajapinta, validointi pyyntö-/vastausmuodoissa
        |
app/services/               Liiketoimintalogiikka: saldon ja varaston päivitys, audit-kirjaukset
        |
app/models/                  SQLAlchemy ORM -mallit (tietokannan rakenne)
        |
PostgreSQL
```

Reitit (`routers/`) eivät koskaan muokkaa tietokantaa suoraan — ne kutsuvat aina
palvelukerrosta (`services/`), joka vastaa transaktioiden eheydestä. Tämä pitää
liiketoimintasäännöt (esim. "ostotapahtuma päivittää sekä saldon että varaston
samassa transaktiossa") yhdessä paikassa testattavana ja ylläpidettävänä.

## Moduulit

- `app/config.py` — ympäristömuuttujista luettu asetukset (Pydantic Settings).
- `app/database.py` — SQLAlchemy async-engine ja istuntotehdas.
- `app/security.py` — PIN-tiivisteet (Argon2) ja allekirjoitetut istuntoevästeet.
- `app/dependencies.py` — FastAPI-riippuvuudet kirjautuneen/admin-käyttäjän hakuun.
- `app/models/` — yksi tiedosto per kokonaisuus: `user.py`, `product.py`, `inventory.py`,
  `recipe.py`, `audit.py`.
- `app/schemas/` — Pydantic-mallit pyyntöjen validointiin ja JSON-vastauksiin.
- `app/services/` — liiketoimintalogiikka: `auth_service`, `kiosk_service`,
  `supply_service`, `inventory_service`, `audit_service`, `analytics_service`,
  `admin_service`, `notification_service` (Signal), `version_service`
  (käynnissä oleva versio + GitHub-vertailu).
- `app/routers/` — yksi reititystiedosto per vastuualue (kioski, tavarantuonti,
  kirjautuminen, sekä erilliset admin-reitit jokaiselle hallintanäkymälle).

## Istunnonhallinta

Kioski on yksi jaettu fyysinen päätelaite. Kirjautuminen luo lyhytikäisen,
allekirjoitetun istuntoevästeen (`itsdangerous`). Eväste poistetaan eksplisiittisesti
aina OK- tai Peruuta-painikkeen painamisen yhteydessä, jolloin käyttäjä kirjautuu
automaattisesti ulos — tätä ei jätetä selaimen istunnon aikakatkaisun varaan.

## Tapahtumaloki keskiössä

`AuditLogEntry`-taulu on järjestelmän totuuden lähde rahaliikenteelle ja
varastomuutoksille. Sovelluskoodi ei koskaan päivitä tai poista rivejä tästä
taulusta — kaikki korjaukset tehdään uusilla, kuittaavilla riveillä. Tämä
mahdollistaa täydellisen jäljitettävyyden ja sen, että tilastot voidaan laskea
uudelleen milloin tahansa suoraan lokista.

## Tilastot vs. totuus

Varaston `quantity_in_stock` on laskennallinen arvio, jota päivitetään jokaisen
myynnin, tavarantuonnin ja ylläpidon korjauksen yhteydessä. Fyysinen inventaario
(`INVENTORY_CORRECTION`) on ainoa asia joka korvaa tämän arvon suoraan — se on
absoluuttinen totuus. Tilastot ja analytiikka (`analytics_service.py`), mukaan
lukien kahvipannujen klusterointiheuristiikka, lasketaan tapahtumalokista
pyynnön hetkellä eivätkä koskaan kirjoita takaisin tietokantaan.

## Teemat

Visuaalinen ilme on jaettu kahteen tasoon: `static/css/base.css` (rakenne ja
komponentit, ei väriarvoja — kaikki nojaa `var(--color-*)`-muuttujiin) ja
`static/css/themes/*.css` (yksi tiedosto per teema, sisältää vain `:root`-värit
ja fontin, plus teemakohtaisia lisäyksiä kuten Maavoimat-teeman camo-tausta).
Uusi teema = uusi tiedosto kansioon, ei koodimuutosta — Asetukset-sivun
pudotusvalikko lukee kansion sisällön ajossa (`theme_service.list_available_themes`).

Aktiivinen teema ei ole selainkohtainen: ylläpitäjä valitsee sen Asetuksista,
palvelin kopioi valitun tiedoston sisällön `static/css/active-theme.css`:ksi
(jonka kaikki sivut lataavat `base.css`:n jälkeen) ja tallentaa valinnan
`app_settings.active_theme`-sarakkeeseen. Koska `active-theme.css` on
gitignoroitu generoitu tiedosto, se rakennetaan uudelleen tietokannan
perusteella aina sovelluksen käynnistyessä (`main.py`:n startup-hook) — fresh
git clone toimii ilman erillistä askelta.

## Signal-ilmoitukset

`app/services/notification_service.py` lähettää valinnaisia Signal-ryhmäviestejä
itsenäisesti hostatun `signal-cli-rest-api`-kontin kautta (linkitetty
toissijaiseksi laitteeksi olemassa olevaan Signal-tiliin, ei erillistä
bottinumeroa). Lähetys on aina parhaan yrityksen periaatteella: epäonnistunut
HTTP-kutsu lokitetaan ja niellään, eikä koskaan kaada ostotapahtumaa, varaston
päivitystä tai kuukausimaksun veloitusta. Jos `SIGNAL_SENDER_NUMBER` tai
`SIGNAL_GROUP_ID` puuttuu asetuksista, lähetysfunktio palaa välittömästi
tekemättä mitään.

## Julkaisuprosessi: dev vs. tuotanto

Kehitys tapahtuu erillisessä ympäristössä (esim. kloonatussa `kahvikassa-dev`
-kontissa), jolla on oma tietokantansa. Kun muutos on valmis, se committoidaan
ja pushataan GitHubiin (`gisestek/kahvikassa`). Tuotantopalvelin päivitetään
ajamalla `./deploy.sh`, joka hakee uusimman koodin, kirjoittaa version
(`VERSION`-tiedosto = lyhyt commit-hash) ja ajaa Alembic-migraatiot.

Tämä erottaa eksplisiittisesti kaksi asiaa, jotka helposti sekoittuvat: **koodi**
siirtyy aina git-pushilla + `deploy.sh`:lla, **data** ei koskaan siirry
automaattisesti ympäristöjen välillä. Migraatiot saavat ainoastaan muuttaa
skeemaa (`CREATE TABLE`, `ALTER TABLE`, ENUM-arvojen lisäys) — ne eivät koskaan
tyhjennä tai korvaa olemassa olevaa dataa. Tuotannon Postgres- ja
signal-cli-volyymit (`kahvikassa_pgdata`, `kahvikassa_signal_data`) pysyvät
koskemattomina jokaisen deployn yli.

`app/services/version_service.py` lukee `VERSION`-tiedoston ja vertaa sitä
GitHubin uusimpaan committiin (parhaan yrityksen periaatteella — verkkovirhe ei
koskaan kaada ylläpitosivua). Ylläpidon etusivu näyttää käynnissä olevan
version ja ilmoittaa, jos GitHubissa on uudempi commit.
