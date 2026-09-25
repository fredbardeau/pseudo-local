"""Couche 3 : remplacement reversible et coherent.

Coherent veut dire deux choses :
  - la meme valeur recoit toujours le meme code dans un document donne ;
  - les variantes d'un meme nom (« Mme Durand », « Claire Durand », « C. Durand »)
    recoivent le meme code, grace a un rapprochement flou.

La numerotation repart de 1 dans CHAQUE categorie : [PERSONNE_001] et [EMAIL_001]
coexistent. C'est plus lisible qu'un compteur global, au prix d'un code un peu
moins robuste si un modele de langage abime le nom de la categorie ; la
reinjection sait rattraper ce cas.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from rapidfuzz import fuzz

from .entites import Entite

#: Categories ou l'on rapproche les variantes d'ecriture.
CATEGORIES_FLOUES = {"PERSONNE", "ORGANISATION"}

#: Categories ou les espaces et separateurs ne comptent pas.
CATEGORIES_NORMALISEES = {"IBAN", "TELEPHONE", "CARTE_BANCAIRE", "NIR", "SIREN", "SIRET"}

CIVILITES = {
    "m", "mr", "mme", "mlle", "monsieur", "madame", "mademoiselle",
    "dr", "docteur", "me", "maitre", "pr", "professeur",
}

AVERTISSEMENT = (
    "Ce fichier contient les valeurs d'origine. Il est la cle qui permet de "
    "re-identifier les personnes : traitez-le comme le document lui-meme. "
    "Tant qu'il existe, le texte pseudonymise reste une donnee a caractere personnel."
)


@dataclass
class Correspondance:
    code: str
    categorie: str
    valeurs: list[str] = field(default_factory=list)

    @property
    def valeur_canonique(self) -> str:
        """La forme la plus longue rencontree : « Claire Durand » plutot que « Durand »."""
        return max(self.valeurs, key=len)


def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def jetons_nom(nom: str) -> list[str]:
    """Decoupe un nom en jetons comparables, civilites retirees."""
    base = _sans_accents(nom).lower()
    bruts = re.split(r"[^a-z0-9]+", base)
    return [j for j in bruts if j and j not in CIVILITES]


def _jetons_compatibles(a: str, b: str) -> bool:
    """« c » couvre « claire » : une initiale vaut le prenom qu'elle abrege."""
    if a == b:
        return True
    if len(a) == 1 and b.startswith(a):
        return True
    if len(b) == 1 and a.startswith(b):
        return True
    return False


def meme_entite(gauche: str, droite: str, seuil: int = 88) -> bool:
    """Deux ecritures designent-elles la meme personne ou la meme structure ?"""
    jg, jd = jetons_nom(gauche), jetons_nom(droite)
    if not jg or not jd:
        return False

    # Cas principal : tous les jetons du nom le plus court se retrouvent dans l'autre.
    court, long = (jg, jd) if len(jg) <= len(jd) else (jd, jg)
    disponibles = list(long)
    for jeton in court:
        for i, candidat in enumerate(disponibles):
            if _jetons_compatibles(jeton, candidat):
                disponibles.pop(i)
                break
        else:
            break
    else:
        return True

    # Filet de securite : fautes de frappe, ordre inverse, particule en trop.
    return fuzz.token_set_ratio(" ".join(jg), " ".join(jd)) >= seuil


def _clef_exacte(categorie: str, texte: str) -> str:
    if categorie in CATEGORIES_NORMALISEES:
        return re.sub(r"[\s.\-]", "", texte).upper()
    if categorie == "EMAIL":
        return texte.strip().lower()
    return " ".join(texte.split())


class TableCorrespondance:
    """Associe chaque valeur reelle a un code, et sait revenir en arriere."""

    def __init__(self, seuil_flou: int = 88):
        self.seuil_flou = seuil_flou
        self._par_code: dict[str, Correspondance] = {}
        self._clefs: dict[tuple[str, str], str] = {}   # (categorie, clef exacte) -> code
        self._compteurs: dict[str, int] = {}

    def code_pour(self, entite: Entite) -> str:
        categorie, texte = entite.categorie, entite.texte
        clef = _clef_exacte(categorie, texte)

        code = self._clefs.get((categorie, clef))
        if code is None and categorie in CATEGORIES_FLOUES:
            code = self._chercher_variante(categorie, texte)

        if code is None:
            self._compteurs[categorie] = self._compteurs.get(categorie, 0) + 1
            code = f"[{categorie}_{self._compteurs[categorie]:03d}]"
            self._par_code[code] = Correspondance(code=code, categorie=categorie)

        self._clefs[(categorie, clef)] = code
        valeurs = self._par_code[code].valeurs
        if texte not in valeurs:
            valeurs.append(texte)
        return code

    def _chercher_variante(self, categorie: str, texte: str) -> str | None:
        for code, corr in self._par_code.items():
            if corr.categorie != categorie:
                continue
            if any(meme_entite(texte, v, self.seuil_flou) for v in corr.valeurs):
                return code
        return None

    # --- lecture ---

    @property
    def correspondances(self) -> dict[str, Correspondance]:
        return dict(self._par_code)

    def valeur(self, code: str) -> str | None:
        corr = self._par_code.get(code)
        return corr.valeur_canonique if corr else None

    # --- persistance ---

    def en_dictionnaire(self) -> dict:
        return {
            "version": 1,
            "cree_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "avertissement": AVERTISSEMENT,
            "seuil_flou": self.seuil_flou,
            "correspondances": {
                code: {"categorie": c.categorie, "valeurs": c.valeurs}
                for code, c in self._par_code.items()
            },
        }

    def enregistrer(self, chemin: Path) -> Path:
        chemin = Path(chemin)
        chemin.write_text(
            json.dumps(self.en_dictionnaire(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        chemin.chmod(0o600)  # lisible par le seul proprietaire
        return chemin

    @classmethod
    def depuis_dictionnaire(cls, donnees: dict) -> "TableCorrespondance":
        table = cls(seuil_flou=donnees.get("seuil_flou", 88))
        for code, c in donnees["correspondances"].items():
            table._par_code[code] = Correspondance(
                code=code, categorie=c["categorie"], valeurs=list(c["valeurs"])
            )
            for valeur in c["valeurs"]:
                table._clefs[(c["categorie"], _clef_exacte(c["categorie"], valeur))] = code
            numero = int(code.rsplit("_", 1)[1].rstrip("]"))
            table._compteurs[c["categorie"]] = max(
                table._compteurs.get(c["categorie"], 0), numero
            )
        return table

    @classmethod
    def charger(cls, chemin: Path) -> "TableCorrespondance":
        return cls.depuis_dictionnaire(
            json.loads(Path(chemin).read_text(encoding="utf-8"))
        )


def appliquer(texte: str, entites: list[Entite],
              table: TableCorrespondance | None = None) -> tuple[str, TableCorrespondance]:
    """Remplace chaque entite par son code. Les entites doivent etre sans chevauchement."""
    table = table or TableCorrespondance()
    codes = [(e, table.code_pour(e)) for e in sorted(entites, key=lambda e: e.debut)]
    morceaux, curseur = [], 0
    for entite, code in codes:
        morceaux.append(texte[curseur:entite.debut])
        morceaux.append(code)
        curseur = entite.fin
    morceaux.append(texte[curseur:])
    return "".join(morceaux), table
