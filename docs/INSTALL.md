# Asennus

## Vaatimukset

- Docker + Docker Compose
- (Kehitykseen) Python 3.12, jos halutaan ajaa ilman Dockeria

## Self-hosted käyttöönotto Docker Composella

1. Kloonaa repo palvelimelle, hakemiston nimen kannattaa olla `kahvikassa`
   (Docker Composen projektin nimi — ja siten volyymien nimet — johdetaan
   hakemiston nimestä, ks. alla "Päivitykset"):

   ```
   git clone https://github.com/gisestek/kahvikassa.git
   cd kahvikassa
   ```

2. Kopioi `.env.example` nimellä `.env` ja aseta oma `SECRET_KEY` (pitkä satunnainen merkkijono):

   ```
   cp .env.example .env
   ```

3. Lisää logo: `static/img/logo.png` (PNG). Etusivu ei toimi täysin oikein ennen tätä.

4. Käynnistä palvelut:

   ```
   docker compose up -d --build
   ```

5. Aja migraatiot konttiin (luo skeeman + esimerkkidatan: kategoriat, ylläpitäjä, esimerkkituotteet):

   ```
   docker compose exec web alembic upgrade head
   ```

6. Avaa selaimessa `http://palvelimen-osoite:8000/`.

   Oletusylläpitäjä migraation jäljiltä: nimi "Ylläpitäjä", PIN `1234`.
   **Vaihda tämä PIN heti ensimmäisen kirjautumisen jälkeen** Käyttäjät-näkymässä.

## Päivitykset (`deploy.sh`)

Kun kehitysversiossa (esim. erillinen `kahvikassa-dev`-kontti) on testattu muutos
valmis, commitoi ja pushaa se GitHubiin. Tuotantopalvelimella päivitys on yksi
komento:

```
./deploy.sh
```

Skripti hakee uusimman koodin (`git fetch` + `git reset --hard origin/master`),
kirjoittaa commit-hashin `VERSION`-tiedostoon, rakentaa `web`-kontin uudelleen,
käynnistää kontit ja ajaa Alembic-migraatiot. **Se ei koskaan kosketa
`kahvikassa_pgdata`- tai `kahvikassa_signal_data`-volyymeja** — vain koodi ja
tietokannan skeema (migraatiot) siirtyvät, ei data. `.env`-tiedosto on
gitignoroitu eikä siis ylikirjoitu päivityksen yhteydessä.

Käynnissä oleva versio (lyhyt commit-hash) näkyy Ylläpito-etusivulla, ja jos
GitHubissa on uudempi commit kuin paikallisesti käytössä, sivu ilmoittaa siitä.

## Signal-ilmoitukset (valinnainen)

Järjestelmä voi lähettää Signal-ryhmäviestin kun varastotuote putoaa hälytysrajan
alle, tai kun kuukausimaksu veloitetaan. Tämä käyttää self-hosted
`signal-cli-rest-api` -konttia (jo mukana `docker-compose.yml`:ssä), joka on
linkitetty toissijaiseksi laitteeksi jonkun olemassa olevaan Signal-tiliin —
viestit näkyvät siis kyseisen henkilön lähettäminä, ei erillisenä "bottina".

1. Hae linkitys-QR-koodi (kontti pitää olla käynnissä):

   ```
   docker compose exec web python -c "
   import httpx
   r = httpx.get('http://signal-cli:8080/v1/qrcodelink?device_name=Kahvikassa-Bot')
   open('/tmp/qr.png','wb').write(r.content)
   "
   docker compose cp web:/tmp/qr.png ./qr.png
   ```

   QR-koodi vanhenee nopeasti (alle minuutissa) — avaa `qr.png` ja skannaa se
   välittömästi Signalissa: **Asetukset → Linkitetyt laitteet → Linkitä uusi laite**.

2. Selvitä lähettäjän numero ja kohderyhmän ID linkitetyltä tililtä:

   ```
   docker compose exec web python -c "
   import httpx
   print(httpx.get('http://signal-cli:8080/v1/accounts').text)
   "
   docker compose exec web python -c "
   import httpx
   print(httpx.get('http://signal-cli:8080/v1/groups/<URL-enkoodattu numero>').text)
   "
   ```

   Etsi tulosteesta haluttu ryhmä nimen perusteella ja poimi sen `id`-kenttä.

3. Lisää `.env`-tiedostoon:

   ```
   SIGNAL_SENDER_NUMBER=+358...
   SIGNAL_GROUP_ID=group.xxxxx...
   ```

4. `docker compose up -d web` — varastotuotteille voi nyt asettaa hälytysrajan
   Varasto-sivulla, ja kuukausimaksun veloitus lähettää ilmoituksen automaattisesti.

Jos `SIGNAL_SENDER_NUMBER` tai `SIGNAL_GROUP_ID` on tyhjä, ilmoitukset jäävät
hiljaisesti lähettämättä — mikään muu toiminnallisuus ei riipu Signalista.

### Lähettäjän vaihtaminen myöhemmin (ilman .env-muokkausta tai uudelleenkäyttöönottoa)

Ylläpito-sivun Asetukset-näkymässä lähettäjän numeron ja ryhmän ID:n voi asettaa
suoraan käyttöliittymästä — tämä yliajaa `.env`-tiedoston arvot tietokannasta.
Kätevä esimerkiksi kun kahvikassan vastuuhenkilö vaihtuu. **Tämä ei kuitenkaan
poista linkitystarvetta**: uuden henkilön Signal-tili on aina ensin linkitettävä
signal-cli-rest-api-instanssiin samalla QR-koodi-menetelmällä kuin alkuperäinen
käyttöönotto (yllä, vaihe 1), ennen kuin hänen numeronsa toimii lähettäjänä.

## Kehitysympäristö ilman Dockeria

```
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
# käynnistä paikallinen PostgreSQL ja päivitä DATABASE_URL .env-tiedostoon
alembic upgrade head
uvicorn app.main:app --reload
```

## Tuotantokäyttöön liittyvää

- Aseta `SESSION_COOKIE_SECURE=true`, kun palvelu on HTTPS:n takana.
- Ota varmuuskopiot `kahvikassa_pgdata`-volyymista säännöllisesti — tapahtumaloki on
  järjestelmän ainoa totuuden lähde rahaliikenteelle.
- Tämä on tarkoitettu suljetulle sisäverkolle / luottamukselliselle työyhteisölle.
  Ei sisällä maksukorttikäsittelyä tai julkista rekisteröitymistä.
