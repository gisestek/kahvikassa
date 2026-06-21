# API

Kaikki rajapinnat palauttavat JSON:ia. Istunto kulkee `kahvikassa_session`-evästeessä.

## Kirjautuminen

- `POST /api/auth/login` — body `{ "user_id": int, "pin": str }` → asettaa istuntoevästeen, palauttaa `{ "redirect_to": "/kioski" }`.
- `POST /api/auth/logout` — poistaa istuntoevästeen.
- `GET /api/auth/me` — nykyisen käyttäjän tiedot ja saldo. Vaatii kirjautumisen.
- `POST /api/auth/change-pin` — body `{ "current_pin": str, "new_pin": str }`. Käyttäjä voi vaihtaa oman
  PIN-koodinsa todistettuaan tuntevansa nykyisen. Uuden PIN-koodin on oltava vähintään 4 merkkiä.

## Kioski

- `GET /api/kiosk/products` — myynnissä olevat tuotteet ryhmiteltynä kolmeen kategoriaan.
- `POST /api/kiosk/checkout` — body `{ "items": [{ "sales_product_id": int, "quantity": int }] }`.
  Vähentää reseptin mukaiset raaka-aineet varastosta, veloittaa saldon, kirjaa
  PURCHASE-tapahtumat, poistaa istuntoevästeen (automaattinen uloskirjautuminen).
- `POST /api/kiosk/cancel` — poistaa istuntoevästeen tekemättä muutoksia.

## Tavaran tuonti

- `GET /api/supply/inventory-items` — pudotusvalikkoa varten.
- `POST /api/supply/ingest` — body `{ "inventory_item_id"?: int, "new_item"?: { "name": str, "unit": "g"|"ml"|"pcs" }, "quantity": str, "total_cost": str }`.
  Joko `inventory_item_id` TAI `new_item`, ei molempia. Kasvattaa varastoa,
  hyvittää käyttäjän saldoa, kirjaa SUPPLY_RESTOCK-tapahtuman. Istunto pysyy
  voimassa — käyttäjä ohjataan takaisin kioskinäkymään uloskirjautumatta.

## Ylläpito (vaatii `is_admin`)

- `GET/POST /api/admin/users`, `PUT /api/admin/users/{id}`
- `POST /api/admin/users/{id}/adjust-balance` — body `{ "amount": str, "description": str }`. `amount` voi olla
  positiivinen (hyvitys) tai negatiivinen (veloitus). Kirjaa ADMIN_ADJUSTMENT-tapahtuman.
- `GET/POST /api/admin/categories`, `PUT /api/admin/categories/{id}`
- `GET/POST /api/admin/products`, `PUT /api/admin/products/{id}` — sisältää `recipe_lines`-listan, joka korvaa tuotteen koko reseptin tallennuksen yhteydessä.
- `GET /api/admin/recipes/products-with-recipes`, `GET /api/admin/recipes/inventory-options`
- `GET/POST /api/admin/inventory`, `POST /api/admin/inventory/correction`, `POST /api/admin/inventory/wastage`
- `PUT /api/admin/inventory/{id}/low-stock-threshold` — body `{ "threshold": str|null }`. Asettaa rajan, jonka
  alle pudottuaan tuotteesta lähetetään Signal-ilmoitus kerran (nollautuu kun varasto nousee yli rajan).
  `null` poistaa hälytyksen käytöstä.
- `GET /api/admin/audit` — query-parametrit: `page` (1-pohjainen, 100 riviä/sivu), `user_id`, `event_type`,
  `sales_product_id`, `inventory_item_id`, `date_from`, `date_to`. Palauttaa
  `{ "items": [...], "total": int, "page": int, "page_size": 100, "total_pages": int }`.
- `GET /api/admin/audit/export.csv` — samat suodatinparametrit (ei sivutusta — vie kaikki suodattimeen
  täsmäävät rivit), palauttaa UTF-8 BOM -etuliitteisen CSV-tiedoston (`Content-Disposition: attachment`).
- `GET /api/admin/analytics/sales-volume`, `/wastage`, `/user-usage`, `/milk-consumption`, `/coffee-pots` — kaikki hyväksyvät `weeks_back`-parametrin.
- `GET/PUT /api/admin/settings` — kuukausimaksun asetukset ja Signal-yliajot: `{ "monthly_fee_amount": str,
  "monthly_fee_active": bool, "signal_sender_number": str|null, "signal_group_id": str|null }`. Signal-kentät
  ovat valinnaisia tietokantayliajoja `.env`-oletuksille — `null`/tyhjä palauttaa .env-arvon käyttöön.
  Lähettäjän numeron vaihtaminen edellyttää, että kyseinen Signal-tili on ensin linkitetty
  signal-cli-rest-api-instanssiin (ks. INSTALL.md) — tämä asetus ei tee linkitystä itse.
- `POST /api/admin/settings/charge-monthly-fee` — veloittaa asetetun kuukausimaksun kertaalleen kaikilta
  aktiivisilta käyttäjiltä (vain jos `monthly_fee_active` on päällä ja summa > 0). Ei ajastettu — admin
  käynnistää manuaalisesti. Palauttaa `{ "charged_count": int }`.

## Virheet

Virhetilanteissa palautetaan `4xx`-tilakoodi ja runko `{ "detail": "selitys suomeksi" }`.
