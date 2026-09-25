"""References de dossier : numeros attribues par une organisation a une personne
ou a son dossier (allocataire, adherent, facture, demande, suivi).

La regle de reference est pseudo/REGLES_REFERENCES.md, sous forme testable ;
ce resume n'en est qu'un apercu. En cas d'ecart, le document fait foi.

Pas de cle de controle, pas de format commun : on ne masque automatiquement que
sur preuve.
  Niveau 1 - un mot declencheur (« reference », « dossier », « n° »...) suivi,
    a quatre mots au plus, d'un numero qui a la forme d'une reference : au moins
    4 chiffres, ou des lettres melees a des chiffres ; ni une date, ni un
    montant, ni un ordinal. Une annee n'est pas exclue : le declencheur leve
    l'ambiguite (« matricule 2019 »).
  Niveau 2 - sans declencheur, une forme tres typee : au moins trois groupes
    separes par « - » ou « / », en majuscules et chiffres, avec au moins une
    lettre et un groupe d'au moins 3 chiffres (« SS-2025-0072 »). Deux groupes
    ne suffisent pas : « JO-2024 », « ISO-9001 », « CERFA-12156 » n'identifient
    personne.
Un numero immediatement precede de loi, decret, arrete, ordonnance ou article
n'est jamais une reference de dossier, quelle que soit la couche qui l'a repere.
  Niveau 3 - une suite isolee de 5 a 12 chiffres que rien n'a masquee est
    SIGNALEE, pas masquee : elle arrive decochee dans le panneau de relecture,
    avec la mention « a trancher ». C'est l'humain qui tranche.
"""

import re

from .entites import Entite

DECLENCHEUR = re.compile(
    r"(?<!\w)(?:(?:r[ée]f[ée]rences?|dossiers?|num[ée]ros?|factures?|"
    r"allocataires?|adh[ée]rents?|b[ée]n[ée]ficiaires?|cotes?|matricules?|demandes?|"
    r"contrats?|conventions?|commandes?|sinistres?|identifiants?|clients?)(?!\w)"
    r"|r[ée]fs?(?!\w)\.?"  # « ref » : le point est de la ponctuation, pas une fin de phrase
    r"|n[°º])",  # symbole numero : n°, N°, nº, Nº, colle au numero ou non
    re.IGNORECASE,
)
MOTS_MAX = 4

_JETON = re.compile(r"[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*")
_GROUPE_ESPACE = re.compile(r"\d{1,3}(?: \d{3})+(?!\d)")  # « 2 450 118 »
_DATE = re.compile(r"\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})|\d{1,2}([\-.])\d{1,2}\1\d{4}"
                   r"|\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}")
_ORDINAL = re.compile(r"\d+(?:e|er|re|ère|ème|eme)", re.IGNORECASE)
_MONTANT_APRES = re.compile(r"\s*(?:€|euros?\b|EUR\b|%|k€)", re.IGNORECASE)

TYPEE = re.compile(r"(?<![\w/\-])[A-Z0-9]+(?:[-/][A-Z0-9]+){2,}(?![\w/\-])")

_MOTS_PUBLICS = r"(?:loi|d[ée]cret|arr[êe]t[ée]|ordonnance|article)"
TEXTE_PUBLIC = re.compile(rf"(?<!\w){_MOTS_PUBLICS}(?!\w)", re.IGNORECASE)
# Le mot, puis au plus le symbole numero et un prefixe de code (« L. »), puis le numero.
_PUBLIC_JUSTE_AVANT = re.compile(
    rf"(?<!\w){_MOTS_PUBLICS}[ ]+(?:[nN][°º][ ]*)?(?:[A-Z]\.[ ]*)?$", re.IGNORECASE)


def forme_de_reference(jeton: str, suite: str) -> bool:
    """Le jeton a-t-il la forme d'une reference ? `suite` = le texte qui le suit."""
    chiffres = sum(c.isdigit() for c in jeton)
    lettres = sum(c.isalpha() for c in jeton)
    if chiffres == 0:
        return False
    if not (chiffres >= 4 or lettres):
        return False
    if _DATE.fullmatch(jeton) or _ORDINAL.fullmatch(jeton):
        return False
    if _MONTANT_APRES.match(suite):
        return False
    return True


def _numero_apres(texte: str, depart: int) -> tuple[int, int] | None:
    """Premier numero en forme de reference dans les MOTS_MAX mots qui suivent."""
    fin_ligne = texte.find("\n", depart)
    fin_ligne = len(texte) if fin_ligne == -1 else fin_ligne
    mots = 0
    for m in re.finditer(r"\S+", texte[depart:fin_ligne]):
        debut = depart + m.start()
        espace = _GROUPE_ESPACE.match(texte, debut)
        if espace and forme_de_reference(espace.group().replace(" ", ""),
                                         texte[espace.end():]):
            return espace.start(), espace.end()
        jeton = _JETON.match(texte, debut + (1 if m.group()[0] in "(«\"'" else 0))
        if jeton and jeton.end() - jeton.start() >= 1 and forme_de_reference(
                jeton.group(), texte[jeton.end():]):
            return jeton.start(), jeton.end()
        if m.group() != ":":
            mots += 1
        if mots >= MOTS_MAX or m.group()[-1] in ".;!?":
            return None
    return None


def detecter(texte: str) -> list[Entite]:
    trouvees = []
    for m in DECLENCHEUR.finditer(texte):
        position = _numero_apres(texte, m.end())
        if position:
            debut, fin = position
            trouvees.append(Entite(debut=debut, fin=fin, categorie="IDENTIFIANT",
                                   texte=texte[debut:fin], source="regle"))
    for m in TYPEE.finditer(texte):
        groupes = re.split(r"[-/]", m.group())
        if (any(c.isalpha() for c in m.group())
                and any(g.isdigit() and len(g) >= 3 for g in groupes)):
            trouvees.append(Entite(debut=m.start(), fin=m.end(), categorie="IDENTIFIANT",
                                   texte=m.group(), source="regle"))
    return trouvees


# Isolee : ni collee a un mot, ni partie d'un nombre decimal (« 12345,50 »).
# Une virgule ou un point de ponctuation apres la serie ne compte pas.
SERIE_NUE = re.compile(r"(?<![\w\-/])(?<!\d[,.])\d{5,12}(?![\w\-/]|[,.]\d)")


def signaler(texte: str, entites: list[Entite]) -> list[Entite]:
    """Series de chiffres nues, non couvertes par une detection. Jamais masquees."""
    signalees = []
    for m in SERIE_NUE.finditer(texte):
        if any(e.debut < m.end() and m.start() < e.fin for e in entites):
            continue
        if _MONTANT_APRES.match(texte, m.end()):
            continue
        signalees.append(Entite(debut=m.start(), fin=m.end(), categorie="IDENTIFIANT",
                                texte=m.group(), source="signalement"))
    return signalees


def ecarter_textes_publics(texte: str, entites: list[Entite]) -> list[Entite]:
    """Retire les IDENTIFIANT qui sont des numeros de loi, decret, article..."""
    gardees = []
    for e in entites:
        if e.categorie == "IDENTIFIANT":
            if (_PUBLIC_JUSTE_AVANT.search(texte, 0, e.debut)
                    or TEXTE_PUBLIC.match(e.texte)):
                continue
        gardees.append(e)
    return gardees
