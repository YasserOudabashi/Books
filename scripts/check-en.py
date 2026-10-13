#!/usr/bin/env python3
"""Confronta la versione inglese di un libro con quella italiana, parte per parte.

Controlla che la traduzione non abbia perso o aggiunto pezzi:
  - stesso numero di titoli, paragrafi, riquadri, tabelle, righe, figure, elenchi;
  - stessi id dei titoli, stessi link e stesse immagini, nello stesso ordine;
  - stessa sequenza di riquadri (etichette tradotte con la tabella qui sotto);
  - ogni numero del testo italiano compare anche in quello inglese (0,46 -> 0.46);
  - nessun resto di italiano (parole frequenti come "della", "che", "sono").

Uso:  python3 scripts/check-en.py [cartella-libro]   (default: libri/la-mente-studiata)
Esce con codice 1 se trova problemi.
"""
import html
import re
import sys
from collections import Counter
from pathlib import Path

LIBRO = Path(sys.argv[1] if len(sys.argv) > 1 else "libri/la-mente-studiata")

ETICHETTE = {
    "[IN DUE PAROLE]": "[IN A NUTSHELL]",
    "[IL PUNTO CHIAVE DEL CAPITOLO]": "[KEY POINT OF THE CHAPTER]",
    "[IL DISEGNO DELL'ESPERIMENTO]": "[THE EXPERIMENTAL DESIGN]",
    "[FORMULA]": "[FORMULA]",
    "[QUESTIONE CONTROVERSA]": "[CONTROVERSIAL QUESTION]",
    "[CONVINZIONE DIFFUSA]": "[COMMON BELIEF]",
    "[ATTENZIONE AL SALTO]": "[MIND THE LEAP]",
    "[REGGE ANCORA?]": "[DOES IT STILL HOLD?]",
    "[NUMERI]": "[NUMBERS]",
    "[MINI-CRONOLOGIA]": "[MINI-TIMELINE]",
}
TAG = ["<h1", "<h2", "<h3", "<p", '<div class="box"', "<table", "<tr", "<figure", "<img", "<li", "<strong"]
# Parole italiane frequenti che in un testo inglese non dovrebbero comparire.
ITALIANO = r"\b(della|delle|degli|dello|nella|nelle|sono|questo|questa|anche|perché|quindi|essere|viene|stato|più|però|cioè|ogni|il|che|dei|gli|una)\b"


def corpo(t):
    s = t.index('<div class="wrap')
    e = t.index('<nav class="pager"') if '<nav class="pager"' in t else t.index("</main>")
    return t[s:e]


def testo(frammento, togli_em=False):
    if togli_em:
        frammento = re.sub(r"<em>.*?</em>", " ", frammento, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", frammento))


def prepara(s):
    # coefficiente binomiale C(9,5): due numeri, non un decimale
    return re.sub(r"C\((\d+),\s*(\d+)\)", r"C(\1 ; \2)", s)


def numeri_it(s):
    s = prepara(s)
    s = re.sub(r"(?<=\d) (?=\d{3}\b)", ".", s)  # 96 485 -> 96.485 (migliaia con spazio)
    out = []
    for m in re.finditer(r"(?<![\w.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\w])|(?<![\w.,])\d+(?:,\d+)?(?![\w])", s):
        out.append(float(m.group(0).replace(".", "").replace(",", ".")))
    return out


def numeri_en(s):
    s = prepara(s)
    out = []
    for m in re.finditer(r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,])\d+(?:\.\d+)?(?:s\b)?(?![\w])|(?<![\w\d])\.\d+", s):
        v = m.group(0)
        if v.endswith("s"):  # 1950s: anche "50" (gli anni '50 dell'originale)
            v = v[:-1]
            out.append(float(int(v) % 100))
        out.append(float(v.replace(",", "")))
    return out


GLOSSARIO = re.compile(r'(<h2 id="cap-Appendice-D-Glossario">.*?)(?=<h2 )', re.S)


def separa_glossario(c):
    """Toglie il glossario dal confronto generale: in inglese le voci sono riordinate
    e i gruppi per lettera (titoli e tabelle) cambiano. Si confronta a parte il numero di voci."""
    m = GLOSSARIO.search(c)
    if not m:
        return c, None
    voci = len([r for r in re.findall(r"<tr>.*?</tr>", m.group(1), re.S) if "<th>" not in r])
    return c[:m.start()] + c[m.end():], voci


def confronta(nome, it, en):
    problemi = []
    (ci, gi), (ce, ge) = separa_glossario(corpo(it)), separa_glossario(corpo(en))
    if gi != ge:
        problemi.append(f"glossario: {gi} voci in italiano, {ge} in inglese")
    for tag in TAG:
        a, b = ci.count(tag), ce.count(tag)
        if a != b:
            problemi.append(f"{tag}: {a} in italiano, {b} in inglese")
    for cosa, rx in (("id", r' id="([^"]+)"'), ("link", r' href="([^"]+)"'), ("immagini", r' src="([^"]+)"')):
        if re.findall(rx, ci) != re.findall(rx, ce):
            problemi.append(f"{cosa} diversi o in ordine diverso")
    lab_it = [ETICHETTE.get(x, x) for x in re.findall(r'class="box-label">([^<]*)', ci)]
    lab_en = re.findall(r'class="box-label">([^<]*)', ce)
    if lab_it != lab_en:
        diff = next((i for i, (a, b) in enumerate(zip(lab_it, lab_en)) if a != b), min(len(lab_it), len(lab_en)))
        problemi.append(f"riquadri diversi dal n. {diff + 1}: atteso {lab_it[diff:diff+1]}, trovato {lab_en[diff:diff+1]}")
    mancano = Counter(numeri_it(testo(ci))) - Counter(numeri_en(testo(ce)))
    if mancano:
        problemi.append("numeri assenti in inglese: " + ", ".join(f"{v:g}" + (f" (x{c})" if c > 1 else "") for v, c in sorted(mancano.items())[:15]))
    resti = re.findall(ITALIANO, testo(ce, togli_em=True), flags=re.I)
    if len(resti) > 3:
        frasi = [m.group(0) for m in re.finditer(r"[^.]{0,40}" + ITALIANO + r"[^.]{0,40}", testo(ce, True), flags=re.I)][:3]
        problemi.append(f"{len(resti)} parole italiane, es.: " + " | ".join(f.strip() for f in frasi))
    return problemi


def main():
    pagine = sorted(p.name for p in LIBRO.glob("*.html"))
    errori = 0
    for nome in pagine:
        en_file = LIBRO / "en" / nome
        if not en_file.exists():
            print(f"MANCA  en/{nome}"); errori += 1; continue
        problemi = confronta(nome, (LIBRO / nome).read_text(encoding="utf-8"), en_file.read_text(encoding="utf-8"))
        print(("OK     " if not problemi else "ERRORE ") + nome)
        for p in problemi:
            print("       - " + p)
        errori += bool(problemi)
    print(f"\n{len(pagine) - errori}/{len(pagine)} pagine senza problemi.")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
