"""Conformite du code a pseudo/REGLES_REFERENCES.md, qui est la SOURCE.

Ce fichier ne contient aucun cas : il les lit dans les blocs ```cas du document.
C'est un test de NON-REGRESSION (cas ecrits par l'auteur du code) : il empeche
la derive, il ne mesure rien.
"""
import re
from pathlib import Path

import pytest

from pseudo.entites import Entite
from pseudo.pipeline import analyser
from pseudo.references import ecarter_textes_publics

DOCUMENT = Path(__file__).parent.parent / "pseudo" / "REGLES_REFERENCES.md"


def _blocs():
    """(section, type de bloc, ligne) pour chaque ligne de cas du document."""
    section, bloc = None, None
    for ligne in DOCUMENT.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("## "):
            section = ligne[3:].strip()
        elif ligne.strip() in ("```cas", "```cas-modele"):
            bloc = ligne.strip()[3:]
        elif ligne.strip() == "```":
            bloc = None
        elif bloc and ligne[:2] in ("+ ", "- "):
            yield section, bloc, ligne[0], ligne[2:].replace("\\n", "\n")


def _cas():
    cas = []
    for section, bloc, signe, corps in _blocs():
        if bloc != "cas":
            continue
        if signe == "+":
            texte, attendu = corps.split(" => ")
            cas.append((section, texte, attendu.split(" ; ")))
        else:
            cas.append((section, corps, []))
    return cas


CAS = _cas()
CAS_MODELE = [corps.split(" => ") for _, bloc, _, corps in _blocs() if bloc == "cas-modele"]


def test_le_document_contient_des_cas():
    assert len(CAS) >= 50
    assert any(s.startswith("Niveau 3") for s, _, _ in CAS)
    assert any(s.startswith("Exclusion") for s, _, _ in CAS)
    assert CAS_MODELE


@pytest.mark.parametrize("section, texte, attendu", CAS,
                         ids=[f"{s[:9]}|{t[:40]}" for s, t, _ in CAS])
def test_conforme_au_document(section, texte, attendu):
    analyse = analyser(texte, avec_modele=False)
    if section.startswith("Niveau 3"):
        obtenu = [e.texte for e in analyse.signalements]
        masquees = {e.texte for e in analyse.entites}
        assert not masquees & set(obtenu), "une serie signalee ne doit jamais etre masquee"
    else:
        obtenu = [e.texte for e in analyse.entites if e.categorie == "IDENTIFIANT"]
    assert obtenu == attendu


@pytest.mark.parametrize("texte, extrait", CAS_MODELE, ids=[t[:40] for t, _ in CAS_MODELE])
def test_detection_du_modele_ecartee(texte, extrait):
    debut = texte.index(extrait)
    modele = Entite(debut, debut + len(extrait), "IDENTIFIANT", extrait, "modele", 0.7)
    assert ecarter_textes_publics(texte, [modele]) == []
