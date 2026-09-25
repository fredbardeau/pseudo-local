"""Remise en place des valeurs reelles dans la reponse d'un modele de langage.

Un modele abime souvent les codes : il ecrit [PERSONNE_1] au lieu de [PERSONNE_001],
[Personne_001], ou colle un code inexistant. On rattrape ce qui est rattrapable
et on SIGNALE tout le reste plutot que de laisser passer en silence.
"""

import re
from dataclasses import dataclass

from .pseudonymisation import TableCorrespondance

#: Attrape [PERSONNE_001] mais aussi [personne 1], [PERSONNE-12], [Adresse_003].
MOTIF_CODE = re.compile(r"\[([A-Za-z][A-Za-z_ \-]{1,30}?)[ _\-]?(\d{1,6})\]")


@dataclass
class Anomalie:
    code_trouve: str
    raison: str
    code_retenu: str | None = None
    #: "verifier" exige un coup d'oeil humain ; "information" est attendu et sans gravite.
    gravite: str = "verifier"


@dataclass
class ResultatReinjection:
    texte: str
    remplaces: int
    anomalies: list[Anomalie]

    @property
    def a_verifier(self) -> list[Anomalie]:
        return [a for a in self.anomalies if a.gravite == "verifier"]

    @property
    def non_mentionnes(self) -> list[Anomalie]:
        return [a for a in self.anomalies if a.gravite == "information"]

    @property
    def sans_probleme(self) -> bool:
        return not self.a_verifier


def reinjecter(texte: str, table: TableCorrespondance) -> ResultatReinjection:
    anomalies: list[Anomalie] = []
    remplaces = 0

    def remplacer(m: re.Match) -> str:
        nonlocal remplaces
        brut = m.group(0)
        categorie = m.group(1).strip().upper().replace(" ", "_").replace("-", "_")
        numero = int(m.group(2))
        canonique = f"[{categorie}_{numero:03d}]"

        valeur = table.valeur(canonique)
        if valeur is None:
            anomalies.append(Anomalie(brut, "code absent de la table de correspondance"))
            return brut

        remplaces += 1
        if brut != canonique:
            anomalies.append(Anomalie(
                brut, "code reecrit par le modele, rattrape automatiquement", canonique
            ))
        return valeur

    resultat = MOTIF_CODE.sub(remplacer, texte)

    # Codes presents dans la table mais absents de la reponse. C'est le cas normal
    # des le que le modele resume ou reformule : on le signale sans le presenter
    # comme un probleme, sinon les vraies alertes se noient dans la liste.
    for code in table.correspondances:
        if code not in texte:
            anomalies.append(Anomalie(
                code, "absent de la reponse (le modele ne l'a pas repris)",
                gravite="information"))

    return ResultatReinjection(texte=resultat, remplaces=remplaces, anomalies=anomalies)
