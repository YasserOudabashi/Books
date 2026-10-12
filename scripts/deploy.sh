#!/usr/bin/env bash
# Deploy del sito dei libri sul VPS: aggiorna il codice, ricostruisce
# l'immagine e riavvia il servizio. Da lanciare sul VPS, nella cartella
# del repo (default /opt/books).
#
#   bash scripts/deploy.sh            # git pull + build + restart + verifica
#   SALTA_PULL=1 bash scripts/deploy.sh   # salta il git pull (file gia' aggiornati)
set -euo pipefail

CARTELLA_REPO="${CARTELLA_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
IMMAGINE="${IMMAGINE:-books-sito}"
SERVIZIO="${SERVIZIO:-books-sito}"
PORTA="${PORTA:-8002}"

cd "$CARTELLA_REPO"
echo "==> Repo: $CARTELLA_REPO"

if [[ "${SALTA_PULL:-0}" != "1" ]]; then
    echo "==> git pull"
    git pull --ff-only
fi

echo "==> docker build -t $IMMAGINE ."
docker build -t "$IMMAGINE" .

echo "==> systemctl restart $SERVIZIO"
sudo systemctl restart "$SERVIZIO"

# Il container riparte in un paio di secondi: attende fino a 30s prima di dire
# che qualcosa non va, invece di dichiarare subito un falso errore.
echo "==> verifica su http://localhost:$PORTA/"
for tentativo in $(seq 1 15); do
    if curl -fsS -o /dev/null "http://localhost:$PORTA/"; then
        echo "OK — il sito risponde (tentativo $tentativo)."
        echo
        echo "Libri pubblicati:"
        for libro in libri/*/; do
            [[ -f "$libro/index.html" ]] && echo "  http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORTA/$(basename "$libro")/"
        done
        exit 0
    fi
    sleep 2
done

echo "ERRORE: il sito non risponde sulla porta $PORTA." >&2
echo "Controlla i log con:  sudo journalctl -u $SERVIZIO -n 50 --no-pager" >&2
exit 1
