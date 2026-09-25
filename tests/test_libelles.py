"""Le libelle d'origine ne doit jamais annoncer une verification qui n'a pas eu lieu."""
import pytest

from pseudo.entites import Entite
from pseudo.interface import _etiquette


@pytest.mark.parametrize("categorie", ["IBAN", "NIR", "SIREN", "SIRET", "CARTE_BANCAIRE"])
def test_cle_verifiee_seulement_avec_somme_de_controle(categorie):
    assert "clé vérifiée" in _etiquette(Entite(0, 5, categorie, "xxxxx", "regle"))


@pytest.mark.parametrize("categorie", ["ADRESSE", "IDENTIFIANT", "EMAIL", "TELEPHONE",
                                       "IP", "PLAQUE", "DATE_NAISSANCE", "CODE_POSTAL_VILLE"])
def test_format_reconnu_pour_les_autres_regles(categorie):
    etiquette = _etiquette(Entite(0, 5, categorie, "xxxxx", "regle"))
    assert "format reconnu" in etiquette and "clé vérifiée" not in etiquette


def test_modele():
    assert "modèle" in _etiquette(Entite(0, 5, "IBAN", "xxxxx", "modele"))


def test_signalement_a_trancher():
    assert "à trancher" in _etiquette(Entite(0, 7, "IDENTIFIANT", "1234567", "signalement"))
