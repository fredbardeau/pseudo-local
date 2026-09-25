"""Adresses postales : reperage par regles, puis assemblage en un seul bloc.

Regle du tout ou rien : une adresse masquee a moitie rassure a tort. Des qu'un
element d'adresse est repere, le bloc entier (voie, complements, code postal,
commune, cedex) devient une seule entite, donc un seul code.

Un bloc n'est retenu que s'il porte un ancrage verifiable par regle :
  - une voie : type de voie suivi d'un nom propre (« place de l'Exemple »),
    numero facultatif (« 3 place de l'Exemple ») ;
  - un code postal suivi d'une commune (regle CODE_POSTAL_VILLE).
Les complements (batiment, etage, BP...) et les adresses vues par le modele ne
font que prolonger un bloc ancre : seuls, ils ne masquent rien. Sans cela, le
modele masquait « Rue barree » ou « 1er etage, salle 4 ».
"""

import re

from .entites import Entite
from .regles import MAJ

#: Types de voie, formes pleines et abregees. « mail » est exclu : trop ambigu
#: avec le courrier electronique.
TYPES_VOIE = (
    r"rue|ruelle|avenue|av\.|boulevard|bd|bld|all[ée]e|impasse|chemin|place|quai|"
    r"route|cours|square|sentier|voie|lieu-dit|hameau|r[ée]sidence|villa|passage|"
    r"esplanade|faubourg|promenade|rond-point|cit[ée]|parvis|traverse|chauss[ée]e"
)

# Un mot du nom de voie : commence par une majuscule ou un chiffre et contient au
# moins une lettre (« Exemple », « Abbe-Gregoire », « 8-Mai-1945 », pas « 44000 »).
_MOT = rf"(?=[\w'’\-]*[^\W\d_])[{MAJ}0-9][\w'’\-]*"
# Particules de liaison, en minuscules : « de la Paix », « de l'Abbe-Gregoire ».
_PARTICULE = r"(?:(?:de[ ]+la|du|des|de|la|le|les|aux|au)[ ]+|(?:de[ ]+l|d|l)['’])"
_NOM = rf"{_PARTICULE}?{_MOT}(?:[ ]+{_PARTICULE}?{_MOT})*"
_NUMERO = r"\d{1,4}(?:[ ]?(?:bis|ter|quater)\b|[A-D]\b)?"

VOIE = re.compile(
    rf"(?<![\w\-])(?:{_NUMERO}[ ]*,?[ ]*)?(?i:{TYPES_VOIE})(?![\w\-])[ ]+{_NOM}"
)

COMPLEMENT = re.compile(
    r"(?<!\w)(?:"
    r"\d{1,2}(?:e|er|[èe]me)[ ]+(?i:[ée]tage)"
    r"|(?i:b[âa]timent|b[âa]t\.|escalier|esc\.|appartement|appt\.?|apt\.?|porte|"
    r"[ée]tage|entr[ée]e)[ ]+\w{1,4}"
    r"|(?:BP|CS|TSA)[ ]?\d{1,6}"
    r")(?!\w)"
)

#: Ce qui peut separer deux elements d'une meme adresse : ponctuation legere et
#: sauts de ligne (adresse sur plusieurs lignes), rien d'autre. Un mot entre
#: deux elements (« ou au ») les separe.
_SEPARATEUR = re.compile(r"[\s,;:–\-]*")
ECART_MAX = 80


def assembler(texte: str, entites: list[Entite]) -> list[Entite]:
    """Remplace les morceaux d'adresse par des blocs d'adresse entiers."""
    # (debut, fin, ancre, entite d'origine ou None)
    elements: list[tuple[int, int, bool, Entite | None]] = []
    for m in VOIE.finditer(texte):
        elements.append((m.start(), m.end(), True, None))
    for m in COMPLEMENT.finditer(texte):
        elements.append((m.start(), m.end(), False, None))
    for e in entites:
        if e.categorie == "CODE_POSTAL_VILLE":
            elements.append((e.debut, e.fin, True, e))
        elif e.categorie == "ADRESSE":
            elements.append((e.debut, e.fin, False, e))

    groupes: list[list[tuple[int, int, bool, Entite | None]]] = []
    for element in sorted(elements, key=lambda x: (x[0], -x[1])):
        if groupes:
            fin_groupe = max(x[1] for x in groupes[-1])
            ecart = texte[fin_groupe:element[0]]
            if element[0] <= fin_groupe or (
                len(ecart) <= ECART_MAX and _SEPARATEUR.fullmatch(ecart)
            ):
                groupes[-1].append(element)
                continue
        groupes.append([element])

    absorbees: set[int] = set()
    blocs: list[Entite] = []
    for groupe in groupes:
        origines = [x[3] for x in groupe if x[3] is not None]
        if not any(x[2] for x in groupe):
            # Aucun ancrage : les adresses du modele sont ecartees, le reste ignore.
            absorbees |= {id(e) for e in origines if e.categorie == "ADRESSE"}
            continue
        if all(x[3] is not None and x[3].categorie == "CODE_POSTAL_VILLE" for x in groupe):
            continue  # un code postal + commune seul garde sa categorie
        debut = min(x[0] for x in groupe)
        fin = max(x[1] for x in groupe)
        # Pas de separateur en bord de bloc (« , » ou espace final).
        while fin > debut and texte[fin - 1] in " ,;:–-\n\t":
            fin -= 1
        absorbees |= {id(e) for e in origines}
        blocs.append(Entite(debut=debut, fin=fin, categorie="ADRESSE",
                            texte=texte[debut:fin], source="regle"))

    return [e for e in entites if id(e) not in absorbees] + blocs
