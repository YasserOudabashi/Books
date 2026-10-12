#!/usr/bin/env python3
"""Genera la home con l'elenco dei libri e la pagina 404.

Scansiona le sottocartelle di `libri/`: ogni cartella che contiene un
`index.html` e' un libro. Titolo e sottotitolo sono letti dall'HTML del libro
stesso (<title> e <p class="subtitle">), la copertina e' il primo file
`img/cover.*` trovato. Nessuna dipendenza esterna: solo libreria standard.

Uso:  python3 scripts/build-index.py [cartella-libri]   (default: libri)
Scrive: <cartella-libri>/index.html e <cartella-libri>/404.html
Entrambi i file sono rigenerati a ogni build Docker, quindi non vanno committati.
"""

import html
import re
import sys
from pathlib import Path

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
SUBTITLE_RE = re.compile(r'class="subtitle"[^>]*>(.*?)<', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
COVER_NAMES = ("cover.png", "cover.jpg", "cover.jpeg", "cover.webp", "cover.svg")


def testo(frammento: str) -> str:
    """Ripulisce un frammento di HTML: via i tag, le entita' e gli spazi doppi."""
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", frammento))).strip()


def leggi_libro(cartella: Path) -> dict | None:
    """Estrae titolo, sottotitolo e copertina da un libro; None se non e' un libro."""
    indice = cartella / "index.html"
    if not indice.is_file():
        return None
    sorgente = indice.read_text(encoding="utf-8", errors="replace")
    titolo = TITLE_RE.search(sorgente)
    sottotitolo = SUBTITLE_RE.search(sorgente)
    copertina = next(
        (f"{cartella.name}/img/{nome}" for nome in COVER_NAMES if (cartella / "img" / nome).is_file()),
        None,
    )
    return {
        "slug": cartella.name,
        "titolo": testo(titolo.group(1)) if titolo else cartella.name,
        "sottotitolo": testo(sottotitolo.group(1)) if sottotitolo else "",
        "copertina": copertina,
        "pagine": len(list(cartella.glob("*.html"))),
    }


STILE = """
:root {
  --bg: #faf6ee; --surface: #f3ede0; --text: #26282d; --muted: #5d6068;
  --line: #ddd3bf; --link: #1b3f9e; --accent: #3b4fb8;
  --shadow: 0 6px 24px rgba(40, 30, 10, .14);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14181f; --surface: #1b212b; --text: #d6dae1; --muted: #9aa3b2;
    --line: #2c3544; --link: #8db4ff; --accent: #8da2ff;
    --shadow: 0 6px 24px rgba(0, 0, 0, .5);
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 3rem 1rem 4rem; background: var(--bg); color: var(--text);
  font-family: Charter, "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 1.125rem; line-height: 1.7; -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 46rem; margin: 0 auto; }
h1 { font-size: clamp(1.9rem, 5vw, 2.6rem); line-height: 1.2; margin: 0 0 .3rem; }
.claim { color: var(--muted); margin: 0 0 2.5rem; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.25rem; }
a.card {
  display: grid; grid-template-columns: 5.5rem 1fr; gap: 1.25rem; align-items: center;
  padding: 1.25rem; border: 1px solid var(--line); border-radius: 12px;
  background: var(--surface); color: inherit; text-decoration: none;
  transition: transform .15s ease, box-shadow .15s ease;
}
a.card:hover, a.card:focus-visible { transform: translateY(-2px); box-shadow: var(--shadow); }
a.card:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.card img {
  width: 100%; aspect-ratio: 2 / 3; object-fit: cover;
  border-radius: 6px; border: 1px solid var(--line); background: var(--bg);
}
.card .senza-copertina {
  aspect-ratio: 2 / 3; border-radius: 6px; border: 1px dashed var(--line);
  display: grid; place-items: center; color: var(--muted); font-size: .8rem;
}
.card h2 { font-size: 1.3rem; margin: 0 0 .2rem; }
.card p { margin: 0; color: var(--muted); font-size: .98rem; }
.card .meta { font-family: ui-sans-serif, system-ui, sans-serif; font-size: .82rem; margin-top: .45rem; }
.vuoto { border: 1px dashed var(--line); border-radius: 12px; padding: 2rem; color: var(--muted); }
footer { margin-top: 3rem; color: var(--muted); font-size: .85rem; }
@media (max-width: 30rem) { a.card { grid-template-columns: 4rem 1fr; gap: .9rem; } }
"""


def pagina(titolo: str, corpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titolo)}</title>
<style>{STILE}</style>
</head>
<body>
<div class="wrap">
{corpo}
</div>
</body>
</html>
"""


def card(libro: dict) -> str:
    copertina = (
        f'<img src="{html.escape(libro["copertina"])}" alt="Copertina di {html.escape(libro["titolo"])}">'
        if libro["copertina"]
        else '<div class="senza-copertina">nessuna<br>copertina</div>'
    )
    sottotitolo = f'<p>{html.escape(libro["sottotitolo"])}</p>' if libro["sottotitolo"] else ""
    pagine = f'{libro["pagine"]} pagine' if libro["pagine"] != 1 else "1 pagina"
    return f"""  <li><a class="card" href="{html.escape(libro['slug'])}/">
    <div>{copertina}</div>
    <div>
      <h2>{html.escape(libro['titolo'])}</h2>
      {sottotitolo}
      <p class="meta">{pagine}</p>
    </div>
  </a></li>"""


def main(argv: list[str]) -> int:
    radice = Path(argv[1] if len(argv) > 1 else "libri")
    if not radice.is_dir():
        print(f"errore: la cartella '{radice}' non esiste", file=sys.stderr)
        return 1

    libri = [libro for cartella in sorted(radice.iterdir()) if cartella.is_dir() and (libro := leggi_libro(cartella))]

    if libri:
        elenco = "<ul>\n" + "\n".join(card(libro) for libro in libri) + "\n</ul>"
    else:
        elenco = '<p class="vuoto">Nessun libro pubblicato: aggiungi una cartella con un <code>index.html</code> dentro <code>libri/</code> e rilancia il deploy.</p>'

    quanti = f"{len(libri)} libro" if len(libri) == 1 else f"{len(libri)} libri"
    (radice / "index.html").write_text(
        pagina(
            "Libri",
            f"""<h1>Libri</h1>
<p class="claim">Biblioteca di libri da leggere nel browser — {quanti}.</p>
{elenco}
<footer>Generato da <code>scripts/build-index.py</code> a ogni deploy.</footer>""",
        ),
        encoding="utf-8",
    )

    (radice / "404.html").write_text(
        pagina(
            "Pagina non trovata",
            """<h1>Pagina non trovata</h1>
<p class="claim">L'indirizzo che hai aperto non esiste su questo server.</p>
<p><a href="/">Torna all'elenco dei libri</a></p>""",
        ),
        encoding="utf-8",
    )

    print(f"index.html e 404.html generati in {radice}/ ({quanti}):")
    for libro in libri:
        print(f"  - {libro['slug']}: {libro['titolo']} ({libro['pagine']} pagine)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
