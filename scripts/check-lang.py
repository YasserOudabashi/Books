#!/usr/bin/env python3
"""Confronta le traduzioni di un libro (inglese, francese) con l'originale italiano, parte per parte.

Controlla che la traduzione non abbia perso o aggiunto pezzi:
  - stesso numero di titoli, paragrafi, riquadri, tabelle, righe, figure, elenchi;
  - stessi id dei titoli, stessi link e stesse immagini, nello stesso ordine;
  - stessa sequenza di riquadri (etichette tradotte con le tabelle qui sotto);
  - ogni numero del testo italiano compare anche nella traduzione, nel formato
    della lingua (inglese 0.46 e 14,000; francese 0,46 e 14 000);
  - nessun resto di italiano (parole frequenti come "della", "che", "sono") e,
    per il francese, nessuna frase rimasta in inglese.

Uso:  python3 scripts/check-lang.py [en|fr|tutte] [cartella-libro]
      (default: tutte le lingue presenti, libri/la-mente-studiata)
Esce con codice 1 se trova problemi.
"""
import html
import re
import sys
from collections import Counter
from pathlib import Path

ARGS = sys.argv[1:]
SCELTA = ARGS.pop(0) if ARGS and ARGS[0] in ("en", "fr", "tutte") else "tutte"
LIBRO = Path(ARGS[0] if ARGS else "libri/la-mente-studiata")

ETICHETTE_EN = {
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
ETICHETTE_FR = {
    "[IN DUE PAROLE]": "[EN DEUX MOTS]",
    "[IL PUNTO CHIAVE DEL CAPITOLO]": "[L'ESSENTIEL DU CHAPITRE]",
    "[IL DISEGNO DELL'ESPERIMENTO]": "[LE PLAN DE L'EXPÉRIENCE]",
    "[FORMULA]": "[FORMULE]",
    "[QUESTIONE CONTROVERSA]": "[QUESTION CONTROVERSÉE]",
    "[CONVINZIONE DIFFUSA]": "[IDÉE REÇUE]",
    "[ATTENZIONE AL SALTO]": "[ATTENTION AU SAUT LOGIQUE]",
    "[REGGE ANCORA?]": "[TIENT-ON ENCORE ?]",
    "[NUMERI]": "[CHIFFRES]",
    "[MINI-CRONOLOGIA]": "[MINI-CHRONOLOGIE]",
}
TAG = ["<h1", "<h2", "<h3", "<p", '<div class="box"', "<table", "<tr", "<figure", "<img", "<li", "<strong"]
# Parole italiane frequenti che in un testo inglese non dovrebbero comparire.
ITALIANO = r"\b(della|delle|degli|dello|nella|nelle|sono|questo|questa|anche|perché|quindi|essere|viene|stato|più|però|cioè|ogni|il|che|dei|gli|una)\b"
# Idem per il francese ("il", "non", "come" esistono anche in francese: tolte).
ITALIANO_FR = r"\b(della|delle|degli|dello|nella|nelle|sono|questo|questa|anche|perché|quindi|essere|viene|stato|più|però|cioè|ogni|che|dei|gli|una|nel|molto|quando|dove)\b"
# Parole inglesi frequenti che in un testo francese non dovrebbero comparire.
INGLESE = r"\b(the|and|which|with|this|these|those|their|there|because|however|between|of the)\b"


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


def numeri_fr(s):
    s = prepara(s)
    s = re.sub(r"(?<=\d)[\xa0\u202f](?=\d{3}\b)", "", s)  # 14 000 (spazio non separabile) -> 14000
    out = []
    for m in re.finditer(r"(?<![\w.,])\d+(?:,\d+)?(?![\w])", s):
        out.append(float(m.group(0).replace(",", ".")))
    # "années 1950-1960" rende anche "anni '50-'60" dell'originale
    for m in re.finditer(r"[Aa]nnées\s+(\d{4}(?:\s*[-–]\s*\d{4})*)", s):
        out.extend(float(int(y) % 100) for y in re.findall(r"\d{4}", m.group(1)))
    return out


def norm_etichetta(x):
    return re.sub(r"[\s\xa0\u202f]+", " ", html.unescape(x)).strip()


LINGUE = {
    "en": dict(nome="inglese", etichette=ETICHETTE_EN, numeri=numeri_en, resti=ITALIANO, altra=None),
    "fr": dict(nome="francese", etichette=ETICHETTE_FR, numeri=numeri_fr, resti=ITALIANO_FR, altra=INGLESE),
}

GLOSSARIO = re.compile(r'(<h2 id="cap-Appendice-D-Glossario">.*?)(?=<h2 )', re.S)


def separa_glossario(c):
    """Toglie il glossario dal confronto generale: in inglese le voci sono riordinate
    e i gruppi per lettera (titoli e tabelle) cambiano. Si confronta a parte il numero di voci."""
    m = GLOSSARIO.search(c)
    if not m:
        return c, None
    voci = len([r for r in re.findall(r"<tr>.*?</tr>", m.group(1), re.S) if "<th>" not in r])
    return c[:m.start()] + c[m.end():], voci


def confronta(nome, it, tr, lingua):
    cfg = LINGUE[lingua]
    nl = cfg["nome"]
    problemi = []
    (ci, gi), (ce, ge) = separa_glossario(corpo(it)), separa_glossario(corpo(tr))
    if gi != ge:
        problemi.append(f"glossario: {gi} voci in italiano, {ge} in {nl}")
    for tag in TAG:
        a, b = ci.count(tag), ce.count(tag)
        if a != b:
            problemi.append(f"{tag}: {a} in italiano, {b} in {nl}")
    for cosa, rx in (("id", r' id="([^"]+)"'), ("link", r' href="([^"]+)"'), ("immagini", r' src="([^"]+)"')):
        if re.findall(rx, ci) != re.findall(rx, ce):
            problemi.append(f"{cosa} diversi o in ordine diverso")
    lab_it = [cfg["etichette"].get(norm_etichetta(x), norm_etichetta(x)) for x in re.findall(r'class="box-label">([^<]*)', ci)]
    lab_tr = [norm_etichetta(x) for x in re.findall(r'class="box-label">([^<]*)', ce)]
    if lab_it != lab_tr:
        diff = next((i for i, (a, b) in enumerate(zip(lab_it, lab_tr)) if a != b), min(len(lab_it), len(lab_tr)))
        problemi.append(f"riquadri diversi dal n. {diff + 1}: atteso {lab_it[diff:diff+1]}, trovato {lab_tr[diff:diff+1]}")
    mancano = Counter(numeri_it(testo(ci))) - Counter(cfg["numeri"](testo(ce)))
    if mancano:
        problemi.append(f"numeri assenti in {nl}: " + ", ".join(f"{v:g}" + (f" (x{c})" if c > 1 else "") for v, c in sorted(mancano.items())[:15]))
    rx = cfg["resti"]
    resti = re.findall(rx, testo(ce, togli_em=True), flags=re.I)
    if len(resti) > 3:
        frasi = [m.group(0) for m in re.finditer(r"[^.]{0,40}" + rx + r"[^.]{0,40}", testo(ce, True), flags=re.I)][:3]
        problemi.append(f"{len(resti)} parole italiane, es.: " + " | ".join(f.strip() for f in frasi))
    if cfg["altra"] and nome != "part14.html":  # nell'appendice E ci sono titoli inglesi di opere
        inglesi = re.findall(cfg["altra"], testo(ce, togli_em=True), flags=re.I)
        if len(inglesi) > 6:
            frasi = [m.group(0) for m in re.finditer(r"[^.]{0,40}" + cfg["altra"] + r"[^.]{0,40}", testo(ce, True), flags=re.I)][:3]
            problemi.append(f"{len(inglesi)} parole inglesi, es.: " + " | ".join(f.strip() for f in frasi))
    return problemi


def controlla(lingua):
    pagine = sorted(p.name for p in LIBRO.glob("*.html"))
    errori = 0
    print(f"=== {LINGUE[lingua]['nome']} ({lingua}/) ===")
    for nome in pagine:
        f = LIBRO / lingua / nome
        if not f.exists():
            print(f"MANCA  {lingua}/{nome}"); errori += 1; continue
        problemi = confronta(nome, (LIBRO / nome).read_text(encoding="utf-8"), f.read_text(encoding="utf-8"), lingua)
        print(("OK     " if not problemi else "ERRORE ") + nome)
        for pr in problemi:
            print("       - " + pr)
        errori += bool(problemi)
    print(f"\n{len(pagine) - errori}/{len(pagine)} pagine senza problemi.\n")
    return errori


def main():
    lingue = [l for l in LINGUE if (SCELTA == "tutte" and (LIBRO / l).is_dir()) or SCELTA == l]
    if not lingue:
        print("Nessuna traduzione trovata in", LIBRO); return 1
    return 1 if sum(controlla(l) for l in lingue) else 0


if __name__ == "__main__":
    sys.exit(main())
