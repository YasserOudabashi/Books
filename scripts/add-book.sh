#!/usr/bin/env bash
# Aggiunge un libro al repo partendo da uno zip (o da una cartella) che
# contiene un index.html. Da lanciare sulla tua macchina, dalla root del repo:
#
#   bash scripts/add-book.sh ~/Downloads/Nuovo_libro.zip nuovo-libro
#
# Lo zip puo' avere i file in radice oppure dentro una sottocartella
# (es. "site/"): lo script trova da solo la cartella con l'index.html.
set -euo pipefail

SORGENTE="${1:-}"
SLUG="${2:-}"

if [[ -z "$SORGENTE" || -z "$SLUG" ]]; then
    echo "Uso: bash scripts/add-book.sh <file.zip|cartella> <slug-url>" >&2
    echo "Esempio: bash scripts/add-book.sh ~/Downloads/libro.zip la-mente-studiata" >&2
    exit 1
fi

# Lo slug finisce nell'URL: solo minuscole, numeri e trattini.
if [[ ! "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    echo "ERRORE: lo slug '$SLUG' non va bene. Usa solo minuscole, numeri e trattini," >&2
    echo "        perche' diventa l'indirizzo del libro (es. /la-mente-studiata/)." >&2
    exit 1
fi

CARTELLA_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINAZIONE="$CARTELLA_REPO/libri/$SLUG"

if [[ -e "$DESTINAZIONE" ]]; then
    echo "ERRORE: '$DESTINAZIONE' esiste gia'." >&2
    echo "        Per aggiornare un libro esistente: rm -rf libri/$SLUG && rilancia questo comando." >&2
    exit 1
fi

TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

if [[ -d "$SORGENTE" ]]; then
    cp -r "$SORGENTE" "$TEMP/estratto"
else
    command -v unzip >/dev/null || { echo "ERRORE: serve 'unzip' (sudo apt install unzip)." >&2; exit 1; }
    mkdir -p "$TEMP/estratto"
    unzip -q "$SORGENTE" -d "$TEMP/estratto"
fi

# Cerca l'index.html meno profondo: la sua cartella e' la radice del sito.
INDICE="$(find "$TEMP/estratto" -name index.html -printf '%d %p\n' 2>/dev/null | sort -n | head -1 | cut -d' ' -f2-)"
if [[ -z "$INDICE" ]]; then
    echo "ERRORE: in '$SORGENTE' non c'e' nessun index.html: non sembra un sito statico." >&2
    exit 1
fi

mkdir -p "$DESTINAZIONE"
# Copia tutto il contenuto della cartella del sito, compresi i file nascosti.
cp -r "$(dirname "$INDICE")"/. "$DESTINAZIONE"/

echo "Libro aggiunto in libri/$SLUG ($(du -sh "$DESTINAZIONE" | cut -f1), $(find "$DESTINAZIONE" -name '*.html' | wc -l) pagine HTML)."
echo
echo "Prossimi passi:"
echo "  1. anteprima locale:  python3 -m http.server 8080 --directory libri   -> http://localhost:8080/$SLUG/"
echo "  2. git add libri/$SLUG && git commit -m \"Aggiunge il libro $SLUG\" && git push"
echo "  3. sul VPS:  cd /opt/books && bash scripts/deploy.sh"
