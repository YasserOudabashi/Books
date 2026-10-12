# Books — un unico container nginx che serve tutti i libri statici.
# RISERVA: il sito e' pubblicato su Cloudflare Pages; questo file serve solo
# per un'anteprima con Docker o per tornare al VPS (vedi README).

# Stage 1: genera la home con l'elenco dei libri e la pagina 404.
# Serve solo in build, cosi' il VPS non ha bisogno di Python installato.
FROM python:3.12-alpine AS indice
WORKDIR /src
COPY libri/ ./libri/
COPY scripts/build-index.py ./scripts/
RUN python3 scripts/build-index.py libri

# Stage 2: l'immagine finale e' solo nginx + i file statici (niente Python).
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=indice /src/libri/ /usr/share/nginx/html/
EXPOSE 80
