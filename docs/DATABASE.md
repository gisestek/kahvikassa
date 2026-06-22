# Tietokanta

PostgreSQL. Skeema hallitaan Alembic-migraatioilla (`alembic/versions/`).

## Taulut

### `users`

| Sarake      | Tyyppi          | Kuvaus |
|-------------|-----------------|--------|
| id          | serial PK       | |
| full_name   | varchar(120)    | |
| pin_hash    | varchar(255)    | Argon2-tiiviste, ei koskaan selväkielistä PIN-koodia |
| balance     | numeric(10,2)   | Käyttäjän saldo, päivitetään transaktionaalisesti audit-kirjausten yhteydessä |
| is_active   | boolean         | Vain aktiiviset käyttäjät näkyvät etusivulla |
| is_admin    | boolean         | Pääsy ylläpitonäkymiin |
| created_at  | timestamptz     | |
| extra_data  | jsonb           | Laajennettavuutta varten, ei käytössä oletuksena |

### `product_categories`

| Sarake     | Tyyppi       | Kuvaus |
|------------|--------------|--------|
| id         | serial PK    | |
| name       | varchar(60)  | "Perustuotteet", "Naposteltavat" tai "Muut" |
| sort_order | integer      | Näyttöjärjestys kioskissa |

### `inventory_items` (Varastoartikkelit)

| Sarake             | Tyyppi            | Kuvaus |
|--------------------|-------------------|--------|
| id                 | serial PK         | |
| name               | varchar(120)      | Uniikki |
| unit               | enum(g, ml, pcs)  | Tiukasti rajattu kolmeen yksikköön |
| quantity_in_stock  | numeric(12,3)     | Laskennallinen varastotaso (arvio paitsi heti inventaarion jälkeen) |
| low_stock_threshold | numeric(12,3), nullable | NULL = ei hälytystä käytössä tälle tuotteelle |
| low_stock_notified | boolean           | Estää toistuvat Signal-ilmoitukset; nollautuu kun varasto nousee rajan yli |
| extra_data         | jsonb             | |

### `sales_products` (Myyntituotteet)

| Sarake       | Tyyppi        | Kuvaus |
|--------------|---------------|--------|
| id           | serial PK     | |
| name         | varchar(120)  | |
| category_id  | FK → product_categories | |
| price        | numeric(10,2) | |
| is_active    | boolean       | |
| is_on_sale   | boolean       | |
| extra_data   | jsonb         | |

Tuote näkyy kioskissa vain kun `is_active = true`, `is_on_sale = true`, sillä on
vähintään yksi `recipe_lines`-rivi, JA kaikkia reseptin raaka-aineita on varastossa
enemmän kuin 0. Tämä viimeinen ehto lasketaan aina pyynnön hetkellä — ei tallenneta
mihinkään — niin tuote katoaa kioskista automaattisesti kun raaka-aine loppuu ja
ilmestyy takaisin automaattisesti kun sitä tuodaan lisää, ilman erillistä
"aktivoi uudelleen" -askelta ylläpitäjälle.

### `recipe_lines` (Reseptit)

| Sarake             | Tyyppi         | Kuvaus |
|--------------------|----------------|--------|
| id                 | serial PK      | |
| sales_product_id   | FK → sales_products | |
| inventory_item_id  | FK → inventory_items | |
| quantity_required  | numeric(12,3)  | Desimaaliarvo, esim. 0.120 |

### `audit_log_entries` (Tapahtumaloki)

| Sarake             | Tyyppi          | Kuvaus |
|--------------------|-----------------|--------|
| id                 | serial PK       | |
| occurred_at        | timestamptz     | Indeksoitu |
| user_id            | FK → users, nullable | |
| event_type         | enum            | PURCHASE, SUPPLY_RESTOCK, INVENTORY_CORRECTION, WASTAGE, ADMIN_ADJUSTMENT, MONTHLY_FEE, SYSTEM_CHANGE |
| sales_product_id   | FK → sales_products, nullable | |
| inventory_item_id  | FK → inventory_items, nullable | |
| quantity           | numeric(12,3), nullable | Positiivinen = lisäys, negatiivinen = vähennys |
| amount             | numeric(10,2), nullable | Positiivinen = saldoon hyvitys, negatiivinen = veloitus |
| description        | text, nullable  | |
| extra_data         | jsonb           | |

Taulu on append-only: rivejä ei koskaan päivitetä tai poisteta sovelluskoodista.

`SYSTEM_CHANGE` on yleiskäyttöinen tapahtumatyyppi kaikelle muulle hallinta- ja
itsepalvelumuutokselle, joka ei ole raha- tai varastotapahtuma omine tyyppeineen:
käyttäjien, tuoteryhmien, myyntituotteiden ja varastotuotteiden luonti/muokkaus,
hälytysrajan ja asetusten päivitys, sekä PIN-koodin vaihto. `description`-kenttä
kertoo mitä tehtiin, `extra_data` sisältää koneluettavan `{"entity", "action", "id"}`
-rakenteen. Tämä pitää enum-tyypin pienenä — uusi hallintatoiminto ei tarvitse
omaa migraatiota.

### `app_settings`

Yhden rivin (id=1) taulu järjestelmän laajuisille asetuksille, joille ei ole muuta
luonnollista kotia.

| Sarake                | Tyyppi         | Kuvaus |
|-----------------------|----------------|--------|
| id                    | integer PK     | Aina 1 |
| monthly_fee_amount    | numeric(10,2)  | Kuukausimaksun suuruus |
| monthly_fee_active    | boolean        | Onko kuukausimaksu käytössä |
| signal_sender_number  | varchar(32), nullable  | Yliajaa `.env`:n `SIGNAL_SENDER_NUMBER`:n, kun asetettu |
| signal_group_id       | varchar(255), nullable | Yliajaa `.env`:n `SIGNAL_GROUP_ID`:n, kun asetettu |
| active_theme          | varchar(50)    | Tiedostonimen vartalo `static/css/themes/`-kansiossa (oletus "gootti") |

Kuukausimaksun veloitus ei ole ajastettu — ylläpitäjä käynnistää sen manuaalisesti
ylläpitopaneelista, joka kirjaa MONTHLY_FEE-tapahtuman jokaiselle aktiiviselle
käyttäjälle.

## Numeeriset tyypit

Rahasummat: `NUMERIC(10,2)`. Varasto- ja reseptimäärät: `NUMERIC(12,3)`, jotta
esimerkiksi 0.12 kpl suodattimia tai 10.0 g kahvia tallentuu tarkasti — ei
liukulukuja, ei pyöristysvirheitä.

## Miksi ei yleisluonteisia "aux"-sarakkeita

Laajennettavuus hoidetaan `extra_data JSONB` -sarakkeilla siellä missä se on
perusteltua, ei nimeämättömillä varasarakkeilla.
