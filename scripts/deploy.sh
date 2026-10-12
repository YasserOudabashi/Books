#!/usr/bin/env bash
# Deploy del sito dei libri, da eseguire SUL VPS nella cartella dei file
# (il workflow GitHub Actions la copia in ~/books e poi lancia questo script).
# Non richiede sudo: basta che l'utente possa usare docker.
#
#   bash ~/books/scripts/deploy.sh
#
# Il container usa --restart unless-stopped: docker lo riavvia da solo se
# cade o se il VPS si riavvia, senza bisogno di un servizio systemd.
set -euo pipefail

CARTELLA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOME="${NOME:-books-sito}"
PORTA="${PORTA:-8002}"

cd "$CARTELLA"
echo "==> Cartella: $CARTELLA"

echo "==> docker build -t $NOME ."
docker build -t "$NOME" .

# Se una volta era stato installato come servizio systemd, il servizio
# ricreerebbe il container vecchio subito dopo averlo rimosso: meglio fermarsi.
if command -v systemctl >/dev/null && systemctl is-active --quiet "$NOME" 2>/dev/null; then
    echo "ERRORE: e' attivo il servizio systemd '$NOME', che entra in conflitto." >&2
    echo "        Disattivalo una volta con: sudo systemctl disable --now $NOME" >&2
    exit 1
fi

echo "==> sostituisco il container $NOME (porta $PORTA)"
docker rm -f "$NOME" >/dev/null 2>&1 || true
docker run -d --name "$NOME" --restart unless-stopped -p "$PORTA:80" "$NOME" >/dev/null

# Verifica dall'interno del container (busybox wget e' sempre presente in
# nginx:alpine), cosi' non dipende da curl installato sul VPS.
echo "==> verifica"
for tentativo in $(seq 1 15); do
    if docker exec "$NOME" wget -q -O /dev/null http://localhost/; then
        echo "OK — nginx risponde (tentativo $tentativo)."
        docker image prune -f >/dev/null   # via le immagini dei deploy precedenti
        exit 0
    fi
    sleep 2
done

echo "ERRORE: nginx non risponde. Log del container:" >&2
docker logs --tail 50 "$NOME" >&2 || true
exit 1
