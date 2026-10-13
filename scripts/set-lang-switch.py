#!/usr/bin/env python3
"""Mette (o aggiorna) il selettore di lingua IT | EN | FR nella barra di ogni pagina del libro.

L'italiano e' nella cartella del libro, le traduzioni in sottocartelle con il codice
della lingua (en/, fr/). Il selettore compare solo per le lingue la cui cartella esiste.
Ogni link porta alla stessa pagina nell'altra lingua; app.js aggiunge il capitolo e
ricorda la scelta. Si puo' rilanciare quando si aggiunge una lingua: sostituisce il
selettore vecchio.

Uso:  python3 scripts/set-lang-switch.py [cartella-libro]   (default: libri/la-mente-studiata)
"""
import re
import sys
from pathlib import Path

LIBRO = Path(sys.argv[1] if len(sys.argv) > 1 else "libri/la-mente-studiata")

# codice, sigla sul pulsante, nome nella lingua stessa, etichetta del gruppo
LINGUE = [("it", "IT", "Italiano", "Lingua"), ("en", "EN", "English", "Language"), ("fr", "FR", "Français", "Langue")]
presenti = [l for l in LINGUE if l[0] == "it" or (LIBRO / l[0]).is_dir()]

VECCHI = re.compile(r'<nav class="lang-switch".*?</nav>\n?|<a class="tb-btn lang-btn".*?</a>\n?', re.S)


def href(da, a, pagina):
    if da == "it":
        return pagina if a == "it" else f"{a}/{pagina}"
    if a == da:
        return pagina
    return f"../{pagina}" if a == "it" else f"../{a}/{pagina}"


def selettore(lingua_pagina, pagina):
    etichetta = next(l[3] for l in LINGUE if l[0] == lingua_pagina)
    link = []
    for codice, sigla, nome, _ in presenti:
        corrente = ' aria-current="page"' if codice == lingua_pagina else ""
        link.append(f'<a class="tb-btn lang-btn" href="{href(lingua_pagina, codice, pagina)}" '
                    f'hreflang="{codice}" lang="{codice}" title="{nome}"{corrente}>{sigla}</a>')
    return f'<nav class="lang-switch" aria-label="{etichetta}">\n' + "\n".join(link) + "\n</nav>\n"


def main():
    n = 0
    for codice, *_ in presenti:
        cartella = LIBRO if codice == "it" else LIBRO / codice
        for f in sorted(cartella.glob("*.html")):
            t = f.read_text(encoding="utf-8")
            t = VECCHI.sub("", t)
            marcatore = '<button class="tb-btn" id="settings-btn"'
            if marcatore not in t:
                print("pulsante impostazioni non trovato in", f); return 1
            t = t.replace(marcatore, selettore(codice, f.name) + marcatore, 1)
            f.write_text(t, encoding="utf-8")
            n += 1
    print(f"selettore aggiornato in {n} pagine ({', '.join(l[1] for l in presenti)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
