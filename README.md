# Books — libri statici sul VPS

Raccolta di libri in HTML, serviti da **un unico container nginx** sul VPS
Infomaniak (lo stesso del calendario VRS), sulla porta **8002**.

- Elenco dei libri: **http://179.237.81.123:8002/**
- Un libro: **http://179.237.81.123:8002/la-mente-studiata/**

**Il deploy è automatico**: ogni push su `main` pubblica il sito sul VPS tramite
GitHub Actions. Aggiungere un libro = aggiungere una cartella in `libri/` e fare
push. Niente porte, container o firewall nuovi, niente SSH a mano.

## Come funziona

```
 tu / Claude              GitHub                                   VPS 179.237.81.123
┌───────────────┐ push  ┌─────────────────────────────┐  SSH     ┌───────────────────────────┐
│ libri/<slug>/ │ ────► │ Books (main)                │ ───────► │ ~/books                   │
└───────────────┘       │ Actions: .github/workflows/ │  tar     │ scripts/deploy.sh         │
                        │          deploy.yml         │          │  docker build             │
                        └─────────────────────────────┘          │  container books-sito     │
                                     ▲                           │  porta 8002 ──► nginx     │
                                     └── verifica http://IP:8002 └───────────────────────────┘
```

1. Ogni libro è una cartella dentro `libri/`, con un `index.html` e i suoi file
   (immagini, css, js). Il nome della cartella — lo *slug* — diventa l'indirizzo:
   `libri/la-mente-studiata/` → `http://IP:8002/la-mente-studiata/`.
2. A ogni push su `main`, il workflow `.github/workflows/deploy.yml`:
   - si collega al VPS in SSH con una chiave salvata nei *secrets* di GitHub;
   - copia i file del repo in `~/books` dell'utente di deploy (con uno scambio
     di cartelle: se la copia si interrompe, la versione online resta intatta);
   - lancia `scripts/deploy.sh` sul VPS, che ricostruisce l'immagine e
     sostituisce il container;
   - controlla **da Internet** che `http://179.237.81.123:8002/` risponda.
3. In fase di build, `scripts/build-index.py` legge `<title>`, sottotitolo e
   copertina di ogni libro e genera la **home con l'elenco** e la pagina **404**.
   Sono rigenerate a ogni deploy (e ignorate da git): nessun elenco da aggiornare.
4. Il `Dockerfile` ha due stage: il primo (Python) genera quelle pagine, il
   secondo copia tutto in `nginx:1.27-alpine`. Sul VPS non serve Python.
5. Il container gira con `--restart unless-stopped`: Docker lo fa ripartire da
   solo se cade o se il VPS si riavvia. Per questo **non serve né un servizio
   systemd né `sudo`** — a differenza di VRS, che usa `vrs-calendario.service`.

Il sito è **pubblico** (chi conosce `IP:8002` lo apre, non c'è login) e in
**HTTP**, come VRS sulla 8001. Vedi [Note e limiti](#note-e-limiti).

## Struttura del repo

| Percorso | A cosa serve |
|----------|--------------|
| `libri/<slug>/` | Un libro: `index.html` + file statici. Lo slug è l'URL. |
| `.github/workflows/deploy.yml` | Deploy automatico sul VPS a ogni push su `main`. |
| `Dockerfile` | Build in due stage: genera l'elenco, poi costruisce l'immagine nginx. |
| `nginx.conf` | Configurazione del server: gzip, cache, 404, nessun elenco cartelle. |
| `scripts/build-index.py` | Genera `libri/index.html` e `libri/404.html` leggendo i libri. |
| `scripts/add-book.sh` | Aggiunge un libro al repo partendo da uno zip o da una cartella. |
| `scripts/deploy.sh` | Gira sul VPS: build, sostituzione del container, verifica. Senza sudo. |

## Configurazione una tantum

Da fare **una sola volta**. Serve il tuo accesso al VPS, quindi è l'unico passo
che nessuno può fare al posto tuo. Dopo, non serve più entrare sul server.

### 1. Sul VPS: crea una chiave dedicata al deploy

```bash
ssh <tuo-utente>@179.237.81.123

# Chiave usata solo da GitHub Actions (senza passphrase: deve funzionare da sola)
ssh-keygen -t ed25519 -C "github-actions-books" -f ~/.ssh/books_deploy -N ""
cat ~/.ssh/books_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Controlla che il tuo utente usi docker senza sudo: deve stampare OK
docker ps >/dev/null && echo OK

whoami                  # → valore di VPS_USER
cat ~/.ssh/books_deploy # → valore di VPS_SSH_KEY (tutto, righe BEGIN/END comprese)
```

Se `docker ps` dà *permission denied*: `sudo usermod -aG docker "$USER"`, poi
esci e rientra in SSH e riprova.

### 2. Su GitHub: salva i due secret

[Books → Settings → Secrets and variables → Actions](https://github.com/YasserOudabashi/Books/settings/secrets/actions)
→ **New repository secret**, due volte:

| Nome | Valore |
|------|--------|
| `VPS_SSH_KEY` | l'output di `cat ~/.ssh/books_deploy`, intero |
| `VPS_USER` | l'output di `whoami` |

Facoltativi, solo se cambiano: `VPS_HOST` (default `179.237.81.123`),
`VPS_PORT` (default `22`), `VPS_KNOWN_HOSTS` (riga di `known_hosts` del VPS, per
fissarne l'impronta invece di leggerla a ogni deploy con `ssh-keyscan`).

Puoi poi cancellare la chiave privata dal VPS (`rm ~/.ssh/books_deploy`): lì
serve solo la pubblica in `authorized_keys`.

### 3. Firewall: apri la porta 8002

```bash
sudo ufw status            # se dice "inactive", salta il comando dopo
sudo ufw allow 8002/tcp
```

Infomaniak ha anche un firewall nel pannello di controllo del VPS: lì la porta
8002 va autorizzata in ingresso (la 8001 di VRS lo è già).

### 4. Primo deploy

[Books → Actions → Deploy sul VPS](https://github.com/YasserOudabashi/Books/actions/workflows/deploy.yml)
→ **Run workflow**. Da qui in avanti parte da solo a ogni push su `main`.

## Aggiungere un nuovo libro

Lo slug è il nome che vuoi nell'URL: minuscole, numeri e trattini
(es. `storia-della-mente`).

```bash
cd <clone di Books>
git pull

# 1. Aggiungi il libro dallo zip (lo script trova da solo la cartella con
#    l'index.html, anche se lo zip ha una sottocartella tipo "site/")
bash scripts/add-book.sh ~/Downloads/Nuovo_libro.zip storia-della-mente

# 2. Anteprima locale, prima di pubblicare
python3 scripts/build-index.py libri      # genera la home anche in locale
python3 -m http.server 8080 --directory libri
#    → http://localhost:8080/  e  http://localhost:8080/storia-della-mente/

# 3. Pubblica: il push fa partire il deploy
git add libri/storia-della-mente
git commit -m "Aggiunge il libro storia-della-mente"
git push
```

Dopo un paio di minuti il libro è online su
**http://179.237.81.123:8002/storia-della-mente/** e compare da solo nella home.
L'esito si vede in [Actions](https://github.com/YasserOudabashi/Books/actions):
spunta verde = pubblicato; il riepilogo del run elenca gli indirizzi dei libri.

Senza lo script, il passo 1 a mano è: crea `libri/storia-della-mente/` e
copiaci il contenuto del sito, in modo che `libri/storia-della-mente/index.html`
esista. Nient'altro da configurare.

### Requisiti del libro

Il libro deve essere **statico e autosufficiente**:

- un `index.html` nella radice della cartella;
- **percorsi relativi** (`img/foto.png`, `style.css`), mai assoluti (`/img/foto.png`):
  un percorso assoluto cercherebbe il file nella radice del server, fuori dalla
  cartella del libro, e si romperebbe;
- nessun backend, nessuna chiamata a un'API, nessun file fuori dalla sua cartella.

Controllo veloce:

```bash
cd libri/<slug>
grep -rnE '(src|href)="/' --include='*.html' .    # percorsi assoluti: non deve stampare nulla
grep -rnE 'https?://' --include='*.html' . | head # risorse esterne (CDN): meglio nessuna
```

## Aggiornare o togliere un libro

```bash
# aggiornare (stesso slug = stesso indirizzo, i link condivisi restano validi)
rm -rf libri/<slug>
bash scripts/add-book.sh ~/Downloads/Libro_v2.zip <slug>
git add -A libri/<slug> && git commit -m "Aggiorna il libro <slug>" && git push

# togliere
git rm -r libri/<slug> && git commit -m "Rimuove il libro <slug>" && git push
```

Il push fa il deploy. Il browser può tenere in cache css/js per un'ora e le
immagini per 30 giorni (vedi `nginx.conf`): se vedi ancora la versione vecchia,
ricarica con `Ctrl+Shift+R`.

## Diagnostica

Il primo posto dove guardare è il run fallito in
[Actions](https://github.com/YasserOudabashi/Books/actions): lo step in rosso dice
cosa non va.

| Step fallito / sintomo | Causa e rimedio |
|------------------------|-----------------|
| **Controlla i secret** | Mancano `VPS_SSH_KEY` o `VPS_USER`: vedi [Configurazione una tantum](#configurazione-una-tantum), passo 2. |
| **Prepara la chiave SSH** — "Impossibile leggere la chiave host" | VPS spento, IP cambiato o porta SSH chiusa/diversa: controlla `VPS_HOST` / `VPS_PORT`. |
| **Verifica accesso SSH** — `Permission denied (publickey)` | La pubblica non è in `~/.ssh/authorized_keys` dell'utente `VPS_USER`, o il secret non contiene la chiave privata intera. |
| **Verifica accesso SSH** — "non puo usare docker senza sudo" | `sudo usermod -aG docker <utente>` sul VPS, una volta. |
| **Build e riavvio** — "servizio systemd 'books-sito'" | Era stata installata una vecchia versione con systemd: `sudo systemctl disable --now books-sito`, una volta. |
| **Build e riavvio** — `port is already allocated` | Qualcos'altro usa la 8002 sul VPS: `sudo ss -ltnp \| grep 8002`. |
| **Verifica dall'esterno** — "non risponde da Internet" | Il sito gira ma il firewall blocca la 8002: passo 3 della configurazione (ufw **e** pannello Infomaniak). |
| Il libro nuovo non compare nella home | Manca `libri/<slug>/index.html`, oppure il deploy di quel push è fallito (guarda Actions). |
| Pagina bianca o immagini mancanti | Percorsi assoluti nell'HTML (vedi [Requisiti del libro](#requisiti-del-libro)); conferma con F12 → Network. |
| `404` aprendo una cartella | In quella cartella manca `index.html`: l'elenco automatico dei file è disattivato di proposito. |

Per guardare sul VPS (solo se serve):

```bash
docker ps --filter name=books-sito              # container attivo e da quanto
docker logs --tail 50 books-sito                # log di nginx
docker exec books-sito ls /usr/share/nginx/html # libri davvero presenti
bash ~/books/scripts/deploy.sh                  # rifà il deploy dei file già copiati
```

## Note e limiti

- **Nessuna autenticazione**: tutto quello che è in `libri/` è pubblico per chi
  conosce l'indirizzo. Il repo GitHub è privato, il sito servito no.
- **HTTP, non HTTPS**: va bene per uso via IP. Per l'HTTPS serve un dominio
  puntato al VPS e un reverse proxy (nginx o Caddy) con Let's Encrypt davanti alle
  porte 8001/8002 — lavoro a parte, valido per tutti i servizi del VPS.
- **Convivenza con VRS**: VRS resta sulla 8001 con il suo servizio systemd. I due
  container sono indipendenti: il deploy di uno non tocca l'altro.
- **Chiave di deploy**: dà accesso SSH al VPS come `VPS_USER`. Se va revocata,
  basta togliere la riga `github-actions-books` da `~/.ssh/authorized_keys`.
- **Peso**: ogni libro con le immagini pesa qualche MB nel repo (`la-mente-studiata`
  circa 7 MB). Con molti libri conviene valutare Git LFS per le immagini.
