"""Enchainement des couches 1 et 2, puis arbitrage."""

import re
from dataclasses import dataclass, field

from . import adresses, references, regles
from .entites import Entite, fusionner
from .modele import SEUIL_DEFAUT


@dataclass
class Analyse:
    texte: str
    entites: list[Entite]
    #: References possibles, jamais masquees d'office : l'humain tranche.
    signalements: list[Entite] = field(default_factory=list)

    def par_categorie(self) -> dict[str, list[Entite]]:
        groupes: dict[str, list[Entite]] = {}
        for e in self.entites:
            groupes.setdefault(e.categorie, []).append(e)
        return groupes


def analyser(texte: str, seuil: float = SEUIL_DEFAUT,
             avec_modele: bool = True) -> Analyse:
    """Couche 1 (regles, dont references de dossier) + couche 2 (modele),
    assemblage des adresses en blocs entiers, retrait des numeros de textes
    publics, puis resolution des chevauchements."""
    trouvees = regles.detecter(texte) + references.detecter(texte)
    if avec_modele:
        from . import modele  # import tardif : ne charge torch que si necessaire

        trouvees += modele.detecter(texte, seuil=seuil)
    trouvees += propager(texte, trouvees)
    trouvees = adresses.assembler(texte, trouvees)
    trouvees = references.ecarter_textes_publics(texte, trouvees)
    entites = fusionner(trouvees)
    return Analyse(texte=texte, entites=entites,
                   signalements=references.signaler(texte, entites))


#: Mots qui ne designent personne a eux seuls : civilites et particules.
_MOTS_NON_DISCRIMINANTS = {
    "M", "Mr", "Mme", "Mlle", "Monsieur", "Madame", "Mademoiselle", "Dr", "Me",
    "Le", "La", "Les", "De", "Du", "Des", "Van", "Von", "Ben", "El", "Al",
}


def _formes_a_propager(entite: Entite) -> set[str]:
    """Les ecritures a rechercher ailleurs dans le document."""
    formes = {entite.texte}
    if entite.categorie == "PERSONNE":
        # Un nom deja identifie doit etre masque meme quand il apparait seul :
        # « Pierre Fictif » en tete de note, puis « Monsieur Fictif » plus bas.
        for mot in re.findall(r"[\w'-]+", entite.texte):
            if len(mot) >= 3 and mot[:1].isupper() and mot not in _MOTS_NON_DISCRIMINANTS:
                formes.add(mot)
    return formes


def propager(texte: str, entites: list[Entite]) -> list[Entite]:
    """Etend chaque nom deja detecte a toutes ses autres occurrences du document.

    Sans cela, un nom de famille reconnu dans « Pierre Fictif » restait en
    clair dans « Monsieur Fictif » quelques lignes plus bas.
    """
    ajouts: list[Entite] = []
    for entite in entites:
        if entite.categorie not in ("PERSONNE", "ORGANISATION"):
            continue
        for forme in _formes_a_propager(entite):
            motif = rf"(?<!\w){re.escape(forme)}(?!\w)"
            for m in re.finditer(motif, texte):
                if m.start() == entite.debut and m.end() == entite.fin:
                    continue
                ajouts.append(Entite(
                    debut=m.start(), fin=m.end(), categorie=entite.categorie,
                    texte=m.group(), source="propagation", score=entite.score,
                ))
    return ajouts
