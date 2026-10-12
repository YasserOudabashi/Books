# Books — libri statici su Cloudflare Pages

Raccolta di libri in HTML, pubblicati **gratis** su **Cloudflare Pages**, in
HTTPS, su un indirizzo del tipo `https://<nome-progetto>.pages.dev`.

- Elenco dei libri: `https://<nome-progetto>.pages.dev/`
- Un libro: `https://<nome-progetto>.pages.dev/la-mente-studiata/`

(`<nome-progetto>` è il nome scelto alla creazione del progetto su Cloudflare:
vedi [Configurazione una tantum](#configurazione-una-tantum).)

**Il deploy è automatico**: ogni push su `main` pubblica il sito. Aggiungere un
libro = aggiungere una cartella in `libri/` e fare push. Niente server, niente
container, niente secret su GitHub.

## Come funziona

```
 tu / Claude              GitHub                     Cloudflare Pages
┌───────────────┐ push  ┌──────────────┐  avvisa   ┌──────────────────────────────────────┐
│ libri/<slug>/ │ ────► │ Books (main) │ ────────► │ 1. clona il repo                     │
└───────────────┘       └──────────────┘           │ 2. python3 scripts/build-index.py    │
                                                   │ 3. pubblica la cartella libri/       │
                                                   │    su https://<nome>.pages.dev       │
                                                   └──────────────────────────────────────┘
```

1. Ogni libro è una cartella dentro `libri/`, con un `index.html` e i suoi file
   (immagini, css, js). Il nome della cartella — lo *slug* — diventa l'indirizzo:
   `libri/la-mente-studiata/` → `https://<nome>.pages.dev/la-mente-studiata/`.
2. Cloudflare è collegato al repo GitHub. A ogni push su `main`:
   - scarica il repo;
   - lancia il **comando di build** `python3 scripts/build-index.py libri`, che
     legge `<title>`, sottotitolo e copertina di ogni libro e genera la **home
     con l'elenco** e la pagina **404** (rigenerate a ogni build e ignorate da
     git: nessun elenco da aggiornare a mano);
   - pubblica il contenuto della cartella **`libri`** sulla sua rete.
3. Un push su un **altro branch** non tocca il sito: Cloudflare crea un'anteprima
   separata (`https://<branch>.<nome>.pages.dev`), utile per controllare prima
   del merge.
4. `libri/_headers` contiene le regole di cache (CSS/JS 1 ora, immagini 30
   giorni; l'HTML viene ricontrollato a ogni visita, così un deploy si vede
   subito). Cloudflare lo legge ma **non** lo pubblica.
5. HTTPS, compressione e pagina 404 li fa Cloudflare da solo.

Il sito è **pubblico** (chi conosce l'indirizzo lo apre, non c'è login).

### Limiti del piano gratuito

| Cosa | Limite gratuito | Oggi |
|------|-----------------|------|
| File per sito | 20.000 | ~180 |
| Peso di un singolo file | 25 MiB | pochi KB/MB |
| Build al mese | 500 | una per push |
| Traffico verso file statici | gratis e illimitato | — |

## Struttura del repo

| Percorso | A cosa serve |
|----------|--------------|
| `libri/<slug>/` | Un libro: `index.html` + file statici. Lo slug è l'URL. |
| `libri/_headers` | Regole di cache e sicurezza per Cloudflare Pages. |
| `scripts/build-index.py` | Genera `libri/index.html` e `libri/404.html` leggendo i libri. È il comando di build di Cloudflare. |
| `scripts/add-book.sh` | Aggiunge un libro al repo partendo da uno zip o da una cartella. |
| `Dockerfile`, `nginx.conf`, `scripts/deploy.sh` | **Riserva**: non usati da Cloudflare. Vedi [Tornare al VPS](#riserva-tornare-al-vps). |

## Configurazione una tantum

Da fare **una sola volta**, nel browser. Serve il tuo account, quindi è l'unico
passo che nessuno può fare al posto tuo.

1. Crea un account gratuito su <https://dash.cloudflare.com/sign-up>.
2. Nel pannello: **Workers & Pages → Create → Pages → Connect to Git**.
   - Se la scheda iniziale propone di creare un *Worker*, cerca il link
     **"Looking to deploy Pages? Get started"** in fondo alla pagina.
3. **Connetti GitHub** e autorizza l'app Cloudflare sul repo `Books` (basta solo
   quello, non serve dare accesso a tutti i repo).
4. Scegli il repo `Books` e compila:

   | Campo | Valore |
   |-------|--------|
   | Project name | il nome che vuoi nell'indirizzo, es. `books` → `books.pages.dev` (se è già preso, Cloudflare aggiunge un suffisso) |
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | `python3 scripts/build-index.py libri` |
   | Build output directory | `libri` |
   | Root directory | lascia vuoto |

5. **Save and Deploy**. Dopo un minuto circa il sito è online; l'indirizzo
   esatto compare nella pagina del progetto.

Da qui in avanti ogni push su `main` pubblica da solo.

### Dominio tuo (facoltativo)

Progetto Pages → **Custom domains → Set up a custom domain**. Se il dominio è
già gestito da Cloudflare il collegamento è automatico, altrimenti Cloudflare ti
dice quale record DNS (`CNAME`) aggiungere dal tuo registrar. HTTPS incluso.

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

Dopo un minuto circa il libro è online su
`https://<nome>.pages.dev/storia-della-mente/` e compare da solo nella home.
L'esito si vede nel pannello Cloudflare → progetto → **Deployments** (e su
GitHub, come spunta accanto al commit).

Senza lo script, il passo 1 a mano è: crea `libri/storia-della-mente/` e
copiaci il contenuto del sito, in modo che `libri/storia-della-mente/index.html`
esista. Nient'altro da configurare.

### Requisiti del libro

Il libro deve essere **statico e autosufficiente**:

- un `index.html` nella radice della cartella;
- **percorsi relativi** (`img/foto.png`, `style.css`), mai assoluti (`/img/foto.png`):
  un percorso assoluto cercherebbe il file nella radice del sito, fuori dalla
  cartella del libro, e si romperebbe;
- nessun backend, nessuna chiamata a un'API, nessun file fuori dalla sua cartella;
- nessun file oltre i 25 MiB.

Controllo veloce:

```bash
cd libri/<slug>
grep -rnE '(src|href)="/' --include='*.html' .    # percorsi assoluti: non deve stampare nulla
grep -rnE 'https?://' --include='*.html' . | head # risorse esterne (CDN): meglio nessuna
find . -type f -size +25M                         # file troppo grandi: non deve stampare nulla
```

**Indirizzi senza `.html`**: Cloudflare accorcia da solo gli indirizzi, quindi
`.../part01.html` diventa `.../part01` (con un redirect). I link relativi dei
libri continuano a funzionare senza modifiche.

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
immagini per 30 giorni (vedi `libri/_headers`): se vedi ancora la versione
vecchia, ricarica con `Ctrl+Shift+R`.

## Diagnostica

Il primo posto dove guardare è il deploy fallito nel pannello Cloudflare →
progetto → **Deployments** → **View details**: il log della build dice cosa non va.

| Sintomo | Causa e rimedio |
|---------|-----------------|
| Build fallita con `python3: not found` | Progetto → **Settings → Variables and Secrets** → aggiungi `PYTHON_VERSION` = `3.12`, poi **Retry deployment**. |
| Build fallita con `SyntaxError` su `dict \| None` | Python troppo vecchio nell'ambiente di build: stessa variabile `PYTHON_VERSION` = `3.12`. |
| Home vuota o "404" sulla radice | **Build output directory** sbagliata: deve essere esattamente `libri` (non `/libri`, non `.`). Settings → Builds → Edit. |
| Il push non fa partire nessun deploy | Branch di produzione diverso da `main`, oppure l'app Cloudflare su GitHub non ha accesso al repo: GitHub → Settings → Applications → Cloudflare Workers and Pages → Configure. |
| Il libro nuovo non compare nella home | Manca `libri/<slug>/index.html`, oppure il deploy di quel push è fallito. |
| Pagina bianca o immagini mancanti | Percorsi assoluti nell'HTML (vedi [Requisiti del libro](#requisiti-del-libro)); conferma con F12 → Network. |
| `404` aprendo una cartella | In quella cartella manca `index.html`: l'elenco dei file non esiste su Pages. |
| Deploy fallito per un file troppo grande | Un file supera i 25 MiB: comprimilo (es. immagini in WebP) o spostalo fuori dal repo. |

## Riserva: tornare al VPS

Prima di Cloudflare il sito girava in un container nginx sul VPS Infomaniak
(`http://179.237.81.123:8002/`), con deploy da GitHub Actions. Il workflow è
stato **rimosso**; restano `Dockerfile`, `nginx.conf` e `scripts/deploy.sh`,
che funzionano ancora.

- **Anteprima con Docker** (identica al vecchio sito):
  ```bash
  docker build -t books-sito . && docker run --rm -p 8080:80 books-sito
  # → http://localhost:8080/
  ```
- **Tornare al deploy sul VPS**: recupera il workflow dalla storia di git
  (`git checkout 3a78dd2 -- .github/workflows/deploy.yml`) e riconfigura i secret
  `VPS_SSH_KEY` / `VPS_USER` come descritto nel README di quel commit
  (`git show 3a78dd2:README.md`).
- **Spegnere il vecchio sito sul VPS**, ora che non serve più (una volta, in SSH):
  ```bash
  docker rm -f books-sito          # ferma e rimuove il container
  sudo ufw delete allow 8002/tcp   # richiude la porta (e anche nel pannello Infomaniak)
  ```
  e su GitHub cancella i secret `VPS_SSH_KEY` / `VPS_USER`, poi togli la riga
  `github-actions-books` da `~/.ssh/authorized_keys` sul VPS.

## Note e limiti

- **Nessuna autenticazione**: tutto quello che è in `libri/` è pubblico per chi
  conosce l'indirizzo. Il repo GitHub è privato, il sito no. Se un giorno serve
  un accesso protetto, Cloudflare Access (gratis fino a 50 utenti) si può mettere
  davanti al progetto senza toccare il codice.
- **Anteprime dei branch pubbliche**: anche gli indirizzi `<branch>.<nome>.pages.dev`
  sono raggiungibili da chiunque li conosca.
- **Peso**: ogni libro con le immagini pesa qualche MB nel repo (`la-mente-studiata`
  circa 7 MB). Con molti libri conviene comprimere le immagini (es. WebP).
