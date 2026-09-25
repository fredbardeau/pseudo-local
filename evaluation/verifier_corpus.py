"""Controle de coherence de la verite terrain, independant du detecteur.

Deux verifications :
1. toute chaine annotee existe bien dans son document ;
2. aucune donnee a format evident (mail, IBAN, telephone, IP, plaque, longue
   suite de chiffres) n'a ete oubliee dans l'annotation.
"""
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).parent
CORPUS = RACINE / "corpus"

# Motifs volontairement grossiers : ils servent a reperer des OUBLIS d'annotation,
# pas a detecter proprement. Le vrai detecteur est dans pseudo/regles.py.
MOTIFS_CONTROLE = {
    "mail": r"[\w.+-]+@[\w-]+\.[a-z]{2,}",
    "iban": r"FR\d{2}[ ]?(?:\d{4}[ ]?){5}\d{3}",
    "telephone": r"(?:\+33[ ]?\d(?:[ ]\d{2}){4}|0\d(?:[ .]\d{2}){4})",
    "ip": r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
    "plaque": r"\b[A-Z]{2}-\d{3}-[A-Z]{2}\b",
    "suite_chiffres": r"\b\d[\d ]{6,}\d\b",
}


def spans_attendus(texte: str, verite: dict) -> list[tuple[int, int, str]]:
    """Resout les annotations en spans concrets, la plus longue gagnant en cas de chevauchement."""
    candidats = []
    for categorie, chaines in verite["directs"].items():
        for chaine in chaines:
            for m in occurrences(texte, chaine):
                candidats.append((m[0], m[1], categorie))
    candidats.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
    retenus: list[tuple[int, int, str]] = []
    for span in candidats:
        if not any(span[0] < r[1] and r[0] < span[1] for r in retenus):
            retenus.append(span)
    return sorted(retenus)


def occurrences(texte: str, chaine: str) -> list[tuple[int, int]]:
    """Toutes les occurrences de `chaine`, avec frontieres de mot quand c'est pertinent."""
    motif = re.escape(chaine)
    if chaine[:1].isalnum():
        motif = r"(?<!\w)" + motif
    if chaine[-1:].isalnum():
        motif = motif + r"(?!\w)"
    return [(m.start(), m.end()) for m in re.finditer(motif, texte)]


def main() -> int:
    if not (RACINE / "verite_terrain.json").exists():
        print("Corpus de test absent (evaluation/corpus/, evaluation/verite_terrain.json) : il reste\n"
              "prive. Ses empreintes sont dans evaluation/EMPREINTES.txt.", file=sys.stderr)
        return 2
    verite = json.loads((RACINE / "verite_terrain.json").read_text(encoding="utf-8"))
    documents = verite["documents"]
    erreurs: list[str] = []
    oublis: list[str] = []

    fichiers = sorted(p.name for p in CORPUS.glob("*.txt"))
    if set(fichiers) != set(documents):
        erreurs.append(f"corpus et verite terrain desynchronises : "
                       f"{set(fichiers) ^ set(documents)}")

    total_spans = 0
    for nom in fichiers:
        texte = (CORPUS / nom).read_text(encoding="utf-8")
        v = documents[nom]

        for categorie, chaines in v["directs"].items():
            for chaine in chaines:
                if not occurrences(texte, chaine):
                    erreurs.append(f"{nom} : annotation introuvable dans le texte "
                                   f"-> {categorie} {chaine!r}")
        for chaine in v["indirects"]:
            if chaine not in texte:
                erreurs.append(f"{nom} : indirect introuvable -> {chaine!r}")

        spans = spans_attendus(texte, v)
        total_spans += len(spans)

        couvert = [False] * len(texte)
        for d, f, _ in spans:
            for i in range(d, f):
                couvert[i] = True
        for nom_motif, motif in MOTIFS_CONTROLE.items():
            for m in re.finditer(motif, texte):
                if not any(couvert[i] for i in range(m.start(), m.end())):
                    oublis.append(f"{nom} : {nom_motif} non annote -> {m.group()!r}")

    print(f"{len(fichiers)} documents, {total_spans} spans attendus apres resolution des chevauchements")
    for e in erreurs:
        print("  ERREUR  ", e)
    for o in oublis:
        print("  OUBLI ? ", o)
    if not erreurs and not oublis:
        print("Verite terrain coherente.")
    return 1 if erreurs or oublis else 0


if __name__ == "__main__":
    sys.exit(main())
