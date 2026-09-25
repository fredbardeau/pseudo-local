"""Couche 2 : detection d'entites par modele local (GLiNER2).

Le modele est charge une seule fois par processus. Il ne voit jamais le reseau :
le paquet `pseudo` a deja impose HF_HUB_OFFLINE=1 a l'import.
"""

import re

from . import CACHE_MODELES
from .entites import Entite

NOM_MODELE = "fastino/gliner2-privacy-filter-PII-multi"

#: Libelles passes au modele, et categorie francaise correspondante.
#: Le modele est zero-shot : « organization » fonctionne bien qu'il ne figure
#: pas dans les 42 types sur lesquels il a ete affine.
ETIQUETTES = {
    "person": "PERSONNE",
    "address": "ADRESSE",
    "organization": "ORGANISATION",
    "city": "LIEU",
    "date_of_birth": "DATE_NAISSANCE",
    "government_id": "IDENTIFIANT",
    "account_id": "IDENTIFIANT",
}

#: Libelle disponible mais desactive par defaut, mesure a l'appui.
#: Sur le corpus de test, l'activer fait gagner 1 donnee masquee sur 195 et
#: ajoute 30 faux positifs : le modele etiquette toutes les dates de reunion et
#: d'echeance, qui n'identifient personne. Le bruit rend la relecture humaine
#: — qui est le vrai filet de securite — beaucoup plus penible.
#: Pour l'activer : ETIQUETTES.update(ETIQUETTES_OPTIONNELLES) avant l'analyse.
ETIQUETTES_OPTIONNELLES = {"sensitive_date": "DATE_SENSIBLE"}

SEUIL_DEFAUT = 0.4

#: mdeberta-v3 accepte 512 jetons. On decoupe bien en dessous pour garder de la
#: marge, les libelles occupant eux aussi de la place dans l'entree du modele.
TAILLE_FRAGMENT = 1000

_modele = None


def charger():
    """Charge le modele (quelques secondes), puis le garde en memoire."""
    global _modele
    if _modele is None:
        from gliner2 import GLiNER2

        if not CACHE_MODELES.exists():
            raise FileNotFoundError(
                f"Modele absent de {CACHE_MODELES}. Lancez d'abord :\n"
                f"    uv run python installer_modele.py"
            )
        _modele = GLiNER2.from_pretrained(NOM_MODELE)
    return _modele


def decouper(texte: str, taille_max: int = TAILLE_FRAGMENT) -> list[tuple[int, str]]:
    """Decoupe le texte en fragments courts, en renvoyant leur decalage d'origine.

    On coupe de preference entre paragraphes, sinon entre lignes, sinon entre
    phrases. Les positions renvoyees par le modele sont ensuite ramenees dans
    le repere du texte complet.
    """
    if len(texte) <= taille_max:
        return [(0, texte)]

    # Bornes de coupure candidates, de la plus franche a la plus fine.
    for separateur in (r"\n\s*\n", r"\n", r"(?<=[.!?])\s+"):
        blocs, curseur = [], 0
        for m in re.finditer(separateur, texte):
            blocs.append((curseur, texte[curseur:m.end()]))
            curseur = m.end()
        blocs.append((curseur, texte[curseur:]))
        if all(len(b) <= taille_max for _, b in blocs):
            break

    # Dernier recours : un bloc sans aucun separateur exploitable est coupe net,
    # de preference entre deux mots. Sans cela le modele tronquerait en silence,
    # et une troncature silencieuse est une donnee personnelle non detectee.
    decoupes = []
    for decalage, bloc in blocs:
        while len(bloc) > taille_max:
            coupe = bloc.rfind(" ", 0, taille_max) + 1 or taille_max
            decoupes.append((decalage, bloc[:coupe]))
            decalage += coupe
            bloc = bloc[coupe:]
        decoupes.append((decalage, bloc))
    blocs = decoupes

    fragments, debut, courant = [], None, ""
    for decalage, bloc in blocs:
        if courant and len(courant) + len(bloc) > taille_max:
            fragments.append((debut, courant))
            debut, courant = decalage, bloc
        else:
            if not courant:
                debut = decalage
            courant += bloc
    if courant:
        fragments.append((debut, courant))
    return fragments


def detecter(texte: str, seuil: float = SEUIL_DEFAUT,
             etiquettes: dict[str, str] | None = None) -> list[Entite]:
    """Renvoie les entites vues par le modele, dans le repere du texte complet."""
    etiquettes = etiquettes or ETIQUETTES
    modele = charger()
    trouvees: list[Entite] = []

    for decalage, fragment in decouper(texte):
        brut = modele.extract_entities(
            fragment, list(etiquettes),
            threshold=seuil, include_confidence=True, include_spans=True,
        )
        for libelle, occurrences in brut.get("entities", {}).items():
            categorie = etiquettes.get(libelle)
            if categorie is None:
                continue
            for o in occurrences:
                debut, fin = decalage + o["start"], decalage + o["end"]
                # Garde-fou : on ne fait confiance a la position que si le texte colle.
                if texte[debut:fin] != o["text"]:
                    continue
                if not plausible(categorie, o["text"]):
                    continue
                trouvees.append(Entite(
                    debut=debut, fin=fin, categorie=categorie,
                    texte=o["text"], source="modele",
                    score=float(o.get("confidence", seuil)),
                ))
    return trouvees


def plausible(categorie: str, texte: str) -> bool:
    """Ecarte deux erreurs recurrentes du modele, observees a l'evaluation.

    - Un nom d'organisation est un nom propre : en francais il porte au moins une
      majuscule. Sans ce filtre, le modele etiquette « mairie », « association »
      ou « prefecture », qui sont des noms communs et n'identifient personne.
    - Une annee seule (« depuis 2024 ») n'est pas une date de naissance.
    """
    if categorie == "ORGANISATION":
        return any(mot[:1].isupper() for mot in re.findall(r"\w+", texte))
    if categorie == "DATE_NAISSANCE":
        return not re.fullmatch(r"\D*\d{4}\D*", texte)
    return True
