# Käyttäjän työnkulut

## 1. Tavallinen ostos (optimoitu nopeudelle)

1. Etusivulla napauta omaa nimeä.
2. Syötä PIN-koodi ja paina Enter.
3. Napauta haluttua tuotetta (esim. "Musta kahvi") — se ilmestyy ostoskoriin.
4. Napauta **OK**.
5. Järjestelmä vähentää reseptin raaka-aineet varastosta, veloittaa saldon,
   kirjaa tapahtuman lokiin ja kirjaa käyttäjän automaattisesti ulos.

Koko kierto on suunniteltu kestämään muutaman sekunnin.

## 2. Oston peruuttaminen

1. Lisää tuotteita koriin (tai ei lisätä lainkaan).
2. Napauta **Peruuta**.
3. Mitään ei tallenneta, käyttäjä kirjautuu ulos.

Kioskinäkymässä on myös erillinen "Kirjaudu ulos" -painike oikeassa yläkulmassa
niitä tilanteita varten, joissa käyttäjä ei ole ostamassa mitään (esim. kävi
vain vaihtamassa PIN-koodin tai tuomassa tavaraa).

## 3. Yksittäisen tuotteen poisto korista

Ostoskorilistassa jokaisen rivin vierellä on "Poista"-painike, joka vähentää
kyseisen tuotteen määrää korissa yhdellä.

## 4. Tavaran tuominen ("Toin tavaraa")

1. Kirjaudu sisään normaalisti.
2. Napauta kioskinäkymän "Toin tavaraa" -linkkiä.
3. Valitse joko:
   - **Täydennä olemassa olevaa** — valitse varastotuote pudotusvalikosta.
   - **Luo uusi** — anna nimi ja valitse yksikkö (g, ml tai pcs).
4. Syötä tuotu määrä ja kokonaishinta (desimaalierottimena pakollisesti piste).
5. Vahvista. Varasto kasvaa, saldo hyvittyy kokonaishinnalla, tapahtuma kirjataan
   lokiin, ja käyttäjä palaa kioskinäkymään (ei kirjaudu ulos — tavaran tuonnin
   jälkeen on tavallista jatkaa esim. kahvin ostamisella).

## 5. PIN-koodin vaihtaminen

1. Kirjaudu sisään ja napauta kioskinäkymän "Vaihda PIN" -linkkiä.
2. Syötä nykyinen PIN-koodi sekä uusi PIN-koodi kahdesti.
3. Vahvista. Nykyinen PIN tarkistetaan ennen vaihtoa, ja uusi PIN tallennetaan
   tiivisteenä (Argon2) — selväkielistä PIN-koodia ei koskaan tallenneta.

## 6. Ylläpitäjän työnkulut

- **Käyttäjät**: luo uusia jäseniä, aseta PIN, aktivoi/deaktivoi, myönnä admin-oikeudet.
  Käyttäjäriviltä voi myös lisätä tai vähentää saldoa suoraan (esim. käteisellä
  maksettu hyvitys, tai virheen korjaus) — kirjataan ADMIN_ADJUSTMENT-tapahtumana.
- **Tuoteryhmät**: muokattavissa (nimi, järjestys). Kioskinäkymässä ryhmän nimeä
  ei näytetä tekstinä — ryhmät erotellaan toisistaan vain ohuella jakoviivalla.
- **Myyntituotteet**: luo/muokkaa tuotteita, hintoja, aktiivisuutta, ja niiden reseptiä
  samalla lomakkeella.
- **Reseptit**: katselunäkymä kaikista tuotteiden resepteistä.
- **Varasto**: tarkastele laskennallista varastotasoa, kirjaa fyysinen inventaario
  (korvaa laskennallisen arvon suoraan) ja kirjaa hävikki. Jokaiselle tuotteelle
  voi asettaa hälytysrajan — kun varasto putoaa rajan alle, lähtee kerran
  Signal-ilmoitus (jos Signal-integraatio on määritetty, ks. INSTALL.md).
- **Tapahtumaloki**: suodata käyttäjän, tapahtumatyypin, tuotteen, varastotuotteen
  ja päivämäärävälin mukaan. Loki kattaa kaikki tietokantaan/Signaliin tehdyt
  muutokset — myös käyttäjien, tuoteryhmien, myyntituotteiden ja varastotuotteiden
  hallinnan sekä PIN-koodin vaihdot (tyyppi "Hallintamuutos"). Näkymä on sivutettu
  100 riviä kerrallaan, ja suodattimiin täsmäävät rivit voi ladata CSV-tiedostona
  "Lataa CSV" -linkistä. Rivejä ei voi muokata tai poistaa — virheet korjataan
  uudella, kuittaavalla kirjauksella (esim. uusi INVENTORY_CORRECTION).
- **Tilastot**: viikkokohtainen myynti, hävikki, käyttäjäkohtainen kulutus,
  maidonkulutus, ja kahvipannujen keittohetkien tilastollinen arvio (ei vaikuta
  varastoon — pelkkä analyyttinen päättely tapahtumalokista).
- **Asetukset**: aseta valinnainen kuukausimaksu (summa + päällä/pois-kytkin).
  Maksua ei veloiteta automaattisesti — admin painaa "Veloita nyt kaikilta
  aktiivisilta käyttäjiltä" -painiketta, joka veloittaa summan kertaalleen
  kaikilta aktiivisilta käyttäjiltä ja kirjaa MONTHLY_FEE-tapahtumat. Jos Signal
  on määritetty, veloituksesta lähtee myös ilmoitus ryhmään.
