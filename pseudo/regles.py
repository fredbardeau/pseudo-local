"""Couche 1 : detection deterministe des identifiants a format fixe.

Chaque motif est volontairement large ; c'est la cle de controle qui fait le tri.
Un motif sans cle de controle (mail, telephone, plaque) est resserre a la place.
"""

import re

from .cles import (
    carte_valide, iban_valide, ip_valide, nir_valide, siren_valide, siret_valide,
)
from .entites import Entite

MOIS = ("janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[uû]t|"
        "septembre|octobre|novembre|d[ée]cembre")

# Majuscules francaises, sans passer par une plage Unicode qui attraperait le signe multiplie.
MAJ = "A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ"

_DATE = (rf"\d{{1,2}}(?:er)?\s+(?:{MOIS})\s+\d{{4}}"
         r"|\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}")

#: (categorie, motif, validateur, numero du groupe a retenir comme span)
REGLES: list[tuple[str, str, object, int]] = [
    ("EMAIL",
     r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w-])",
     None, 0),

    ("IBAN",
     rf"(?<![{MAJ}0-9])[A-Z]{{2}}\d{{2}}(?:[ ]?[A-Z0-9]{{2,4}}){{2,8}}(?![A-Z0-9])",
     iban_valide, 0),

    ("NIR",
     r"(?<!\d)[12][ .]?\d{2}[ .]?\d{2}[ .]?(?:\d{2}|2[AB])[ .]?\d{3}[ .]?\d{3}[ .]?\d{2}(?!\d)",
     nir_valide, 0),

    ("SIRET",
     r"(?<!\d)\d{3}[ ]?\d{3}[ ]?\d{3}[ ]?\d{5}(?!\d)",
     siret_valide, 0),

    ("SIREN",
     r"(?<!\d)\d{3}[ ]?\d{3}[ ]?\d{3}(?!\d)",
     siren_valide, 0),

    ("CARTE_BANCAIRE",
     r"(?<!\d)(?:\d{4}[ \-]?){3}\d{4}(?!\d)",
     carte_valide, 0),

    # Fixe et mobile francais : 0X suivi de quatre paires.
    ("TELEPHONE",
     r"(?<![\d+])0[1-9](?:[ .\-]?\d{2}){4}(?!\d)",
     None, 0),

    # International, indicatif + 6 a 14 chiffres. Couvre +33 6 39 98 56 78.
    ("TELEPHONE",
     r"\+\d{1,3}(?:[ .\-]?\d){6,14}(?!\d)",
     None, 0),

    # Le garde-fou de fin doit laisser passer le point final d'une phrase
    # (« ... en 192.168.14.27. Pensez a ») tout en refusant un cinquieme octet.
    ("IP",
     r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?!\.?\d)",
     ip_valide, 0),

    # Plaque francaise depuis 2009. Les plaques d'avant 2009 (123 ABC 45) ne sont
    # pas couvertes : le motif serait trop proche d'une reference de dossier.
    ("PLAQUE",
     rf"(?<![{MAJ}0-9\-])[A-Z]{{2}}-\d{{3}}-[A-Z]{{2}}(?![{MAJ}0-9\-])",
     None, 0),

    # Date de naissance : uniquement en contexte, jamais une date isolee.
    ("DATE_NAISSANCE",
     rf"(?:n[ée]e?s?\s+le|date\s+de\s+naissance\s*:?)\s*({_DATE})",
     None, 1),

    # Code postal suivi d'une commune. Le determinant initial (Le Mans, La Rochelle)
    # est rattache ; le motif s'arrete a toute virgule ou fin de ligne. Forme
    # internationale « F-00100 Nullepart » et mention « Cedex 1 » comprises.
    ("CODE_POSTAL_VILLE",
     rf"(?:(?<![\w\-])F-)?(?<!\d)\d{{5}}(?!\d)[ ]+(?:(?:Le|La|Les|Saint|Sainte|St|Ste)[ \-])?"
     rf"[{MAJ}][\w'’\-]*(?:[ ]+(?i:cedex)(?:[ ]+\d{{1,2}}(?!\d))?)?",
     None, 0),
]

_COMPILEES = [
    (categorie, re.compile(motif, re.IGNORECASE if categorie == "DATE_NAISSANCE" else 0),
     validateur, groupe)
    for categorie, motif, validateur, groupe in REGLES
]


def detecter(texte: str) -> list[Entite]:
    """Applique toutes les regles. Le tri des chevauchements est fait par `fusionner`."""
    trouvees: list[Entite] = []
    for categorie, motif, validateur, groupe in _COMPILEES:
        for m in motif.finditer(texte):
            brut = m.group(groupe)
            if validateur is not None and not validateur(brut):
                continue
            trouvees.append(Entite(
                debut=m.start(groupe), fin=m.end(groupe),
                categorie=categorie, texte=brut, source="regle",
            ))
    return trouvees
