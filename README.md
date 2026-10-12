# Books — libri statici sul VPS

Raccolta di libri in HTML, serviti da **un unico container nginx** sul VPS
Infomaniak (lo stesso del calendario VRS), sulla porta **8002**.

- Elenco dei libri: **http://179.237.81.123:8002/**
- Un libro: **http://179.237.81.123:8002/la-mente-studiata/**

Aggiungere un libro non richiede né una porta nuova, né un container nuovo,
né toccare il firewall: si aggiunge una cartella dentro `libri/` e si rilancia il
deploy. Vedi [Aggiungere un nuovo libro](#aggiungere-un-nuovo-libro).

## Come funziona

```
 la tua macchina                GitHub                     VPS 179.237.81.123
┌─────────────────┐          ┌──────────┐                ┌──────────────────────────┐
│ libri/<slug>/   │  push    │  Books   │   git pull      │ /opt/books               │
│  index.html ... │ ───────► │  (repo)  │ ──────────────► │   docker build           │
└─────────────────┘          └──────────┘                 │   systemctl restart      │
                                                          │   container books-sito   │
                                                          │   porta 8002 ──► nginx   │
                                                          └──────────────────────────┘
```

1. Ogni libro è una cartella dentro `libri/`, con un `index.html` e i suoi file
   (immagini, css, js). Il nome della cartella — lo *slug* — diventa l'indirizzo:
   `libri/la-mente-studiata/` → `http://IP:8002/la-mente-studiata/`.
2. In fase di build, `scripts/build-index.py` legge il `<title>` e il
   sottotitolo di ogni libro e genera la **home con l'elenco** (`libri/index.html`)
   e la pagina **404**. Sono file rigenerati a ogni deploy, quindi non sono
   committati (vedi `.gitignore`): non serve aggiornare nessun elenco a mano.
3. Il `Dockerfile` ha due stage: il primo (Python) genera quelle due pagine, il
   secondo copia tutto in `nginx:1.27-alpine`. L'immagine finale contiene solo
   nginx e i file statici — **sul VPS non serve Python installato**.
4. Il servizio systemd `books-sito` tiene in piedi il container e lo riavvia se
   cade, esattamente come `vrs-calendario` fa con il calendario.

Il sito è **pubblico**: chi conosce `IP:8002` lo apre, non c'è login. È in
**HTTP**, non HTTPS (come VRS sulla 8001). Vedi [Note e limiti](#note-e-limiti).

## Struttura del repo

| Percorso | A cosa serve |
|----------|--------------|
| `libri/<slug>/` | Un libro: `index.html` + file statici. Lo slug è l'URL. |
| `Dockerfile` | Build in due stage: genera l'elenco, poi costruisce l'immagine nginx. |
| `nginx.conf` | Configurazione del server: gzip, cache, 404, nessun elenco cartelle. |
| `scripts/build-index.py` | Genera `libri/index.html` e `libri/404.html` leggendo i libri. |
| `scripts/add-book.sh` | Aggiunge un libro al repo partendo da uno zip o da una cartella. |
| `scripts/deploy.sh` | Da lanciare sul VPS: `git pull` → `docker build` → restart → verifica. |
| `deploy/books-sito.service` | Unit systemd da copiare in `/etc/systemd/system/`. |

## Prima installazione sul VPS (una volta sola)

Da fare una volta sola, in SSH sul VPS. I passi 1–3 richiedono `sudo`.

```bash
ssh <utente>@179.237.81.123

# 1. Clona il repo in /opt/books (stesso schema di /opt/vrs-calendario)
sudo git clone https://github.com/YasserOudabashi/books.git /opt/books
sudo chown -R "$USER":"$USER" /opt/books
cd /opt/books

# 2. Costruisci l'immagine e installa il servizio
docker build -t books-sito .
sudo cp deploy/books-sito.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now books-sito

# 3. Apri la porta 8002 nel firewall (solo se c'è ufw attivo)
sudo ufw status                 # se dice "inactive", salta il comando dopo
sudo ufw allow 8002/tcp

# 4. Verifica
sudo systemctl status books-sito --no-pager
curl -I http://localhost:8002/
```

Poi apri **http://179.237.81.123:8002/** dal browser.

> Se dal browser non si apre ma `curl -I http://localhost:8002/` sul VPS
> risponde `200 OK`, il problema è il firewall: oltre a `ufw` sul server,
> Infomaniak ha un firewall nel pannello di controllo del VPS, dove la porta
> 8002 va autorizzata in ingresso (la 8001 di VRS lo è già).

## Aggiungere un nuovo libro

Questa è la procedura da seguire ogni volta che c'è un libro nuovo. Lo slug è
il nome che vuoi nell'URL: minuscole, numeri e trattini (es. `storia-della-mente`).

### Sulla tua macchina

```bash
cd <cartella dove hai clonato Books>
git pull

# 1. Aggiungi il libro partendo dallo zip (lo script trova da solo la cartella
#    con l'index.html, anche se lo zip ha una sottocartella tipo "site/")
bash scripts/add-book.sh ~/Downloads/Nuovo_libro.zip storia-della-mente

# 2. Controlla il risultato in locale, prima di pubblicare
python3 -m http.server 8080 --directory libri
#    → http://localhost:8080/storia-della-mente/
#    (la home con l'elenco in locale non si vede: la genera la build.
#     Per vederla anche in locale: python3 scripts/build-index.py libri)

# 3. Pubblica su GitHub
git add libri/storia-della-mente
git commit -m "Aggiunge il libro storia-della-mente"
git push
```

Senza lo script, il passo 1 a mano è: crea `libri/storia-della-mente/` e
copiaci dentro il contenuto del sito, in modo che `libri/storia-della-mente/index.html`
esista. Nient'altro: niente file di configurazione da aggiornare.

### Sul VPS

```bash
ssh <utente>@179.237.81.123
cd /opt/books
bash scripts/deploy.sh
```

Lo script fa `git pull`, ricostruisce l'immagine, riavvia il servizio, aspetta
che il sito risponda e stampa gli indirizzi dei libri pubblicati. Il nuovo libro
compare da solo nella home: **http://179.237.81.123:8002/storia-della-mente/**.

A mano, gli stessi tre comandi sono:

```bash
cd /opt/books && git pull && docker build -t books-sito . && sudo systemctl restart books-sito
```

### Requisiti del libro

Il libro deve essere **statico e autosufficiente**:

- un `index.html` nella radice della cartella;
- **percorsi relativi** (`img/foto.png`, `style.css`), mai assoluti (`/img/foto.png`):
  un percorso assoluto cercherebbe il file nella radice del server, fuori dalla
  cartella del libro, e si romperebbe;
- nessun backend, nessuna chiamata a un'API, nessun file fuori dalla sua cartella.

Per controllare in fretta se un libro rispetta le ultime due condizioni:

```bash
cd libri/<slug>
grep -rnE '(src|href)="/' --include='*.html' .    # percorsi assoluti: non deve stampare nulla
grep -rnE 'https?://' --include='*.html' . | head # risorse esterne (CDN): meglio nessuna
```

## Aggiornare un libro già pubblicato

```bash
# sulla tua macchina, dalla root del repo
rm -rf libri/<slug>
bash scripts/add-book.sh ~/Downloads/Libro_v2.zip <slug>
git add -A libri/<slug>
git commit -m "Aggiorna il libro <slug>"
git push

# sul VPS
cd /opt/books && bash scripts/deploy.sh
```

Lo slug invariato mantiene lo stesso indirizzo, quindi i link già condivisi
continuano a funzionare. Il browser può tenere in cache css/js per un'ora e le
immagini per 30 giorni (vedi `nginx.conf`): se dopo il deploy vedi ancora la
versione vecchia, ricarica con `Ctrl+Shift+R`.

## Togliere un libro

```bash
git rm -r libri/<slug>
git commit -m "Rimuove il libro <slug>"
git push
# sul VPS
cd /opt/books && bash scripts/deploy.sh
```

## Diagnostica

| Sintomo | Causa probabile e rimedio |
|---------|---------------------------|
| Il browser non apre `IP:8002` ma `curl http://localhost:8002/` sul VPS funziona | Firewall: `sudo ufw allow 8002/tcp` **e** la porta 8002 autorizzata nel pannello Infomaniak. |
| `systemctl status books-sito` dice `failed` | Log: `sudo journalctl -u books-sito -n 50 --no-pager`. Spesso è la porta già occupata: `sudo ss -ltnp \| grep 8002`. |
| `docker: Error response ... port is already allocated` | Un container vecchio è rimasto in piedi: `docker rm -f books-sito`, poi `sudo systemctl restart books-sito`. |
| Il libro nuovo non compare nella home | L'elenco si genera in build: hai rilanciato `docker build` (cioè `scripts/deploy.sh`) dopo il `git pull`? Verifica anche che esista `libri/<slug>/index.html`. |
| Pagina del libro bianca, o immagini mancanti | Percorsi assoluti nell'HTML del libro (vedi [Requisiti del libro](#requisiti-del-libro)). Conferma con la console del browser (F12), tab Network. |
| `404` aprendo una cartella | In quella cartella manca `index.html`: l'elenco automatico dei file è disattivato di proposito. |
| Il deploy non trova `git pull` perché ci sono modifiche locali sul VPS | Sul VPS non si modificano i file: `git -C /opt/books checkout -- .` e rilancia. |

Comandi utili sul VPS:

```bash
sudo systemctl status books-sito --no-pager     # stato del servizio
sudo journalctl -u books-sito -f                # log in tempo reale
docker ps | grep books-sito                     # container attivo
docker exec books-sito ls /usr/share/nginx/html # libri davvero presenti nell'immagine
```

## Note e limiti

- **Nessuna autenticazione**: tutto quello che metti in `libri/` è pubblico per
  chi conosce l'indirizzo. Non pubblicare qui materiale che non può essere letto
  da chiunque. Il repo GitHub è privato, il sito servito no.
- **HTTP, non HTTPS**: va bene per uso interno via IP. Per avere HTTPS serve un
  dominio puntato al VPS e un reverse proxy (nginx o Caddy) davanti alle porte
  8001/8002 con certificato Let's Encrypt — lavoro a parte, da fare una volta
  per tutti i servizi del VPS.
- **Convivenza con VRS**: VRS resta sulla 8001 con il suo servizio e il suo
  container. I due sono indipendenti: riavviare uno non tocca l'altro.
- **Peso**: ogni libro con le immagini pesa qualche MB nel repo (`la-mente-studiata`
  circa 7 MB). Con molti libri conviene valutare Git LFS per le immagini.
