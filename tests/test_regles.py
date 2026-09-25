"""Toutes les valeurs sont FICTIVES."""
import pytest

from pseudo.entites import fusionner
from pseudo.regles import detecter


def cats(texte):
    return {(e.categorie, e.texte) for e in fusionner(detecter(texte))}


def test_mail():
    assert ("EMAIL", "claire.durand@example.org") in cats(
        "Ecrivez a claire.durand@example.org."
    )


@pytest.mark.parametrize("brut", [
    "06 39 98 56 78", "06.39.98.56.78", "0639985678", "05-36-49-22-17",
    "+33 6 39 98 77 25", "+33639985678", "+33 1 99 00 45 67",
])
def test_telephone(brut):
    assert any(c == "TELEPHONE" for c, _ in cats(f"Joignable au {brut} la journee."))


def test_iban_espace_ou_non():
    for brut in ["ZZ43 0000 0000 0000 0000 0000 123", "ZZ4300000000000000000000123"]:
        assert ("IBAN", brut) in cats(f"IBAN : {brut}.")


def test_iban_faux_rejete():
    """Une suite qui ressemble a un IBAN mais dont la cle est fausse est ignoree."""
    assert not any(c == "IBAN" for c, _ in cats("IBAN : ZZ4300000000000000000000124."))


def test_nir():
    assert ("NIR", "2 78 05 99 999 042 42") in cats("NIR 2 78 05 99 999 042 42 verifie.")
    assert not any(c == "NIR" for c, _ in cats("NIR 2 78 05 99 999 042 43 verifie."))


def test_siren_siret_ne_se_confondent_pas():
    trouve = cats("SIRET 12002701600563 et SIREN 120027016.")
    assert ("SIRET", "12002701600563") in trouve
    assert ("SIREN", "120027016") in trouve


def test_carte():
    assert ("CARTE_BANCAIRE", "4242 4242 4242 4242") in cats("carte 4242 4242 4242 4242")
    assert not any(c == "CARTE_BANCAIRE" for c, _ in cats("carte 4242 4242 4242 4243"))


def test_carte_dans_un_iban_absorbee_par_l_iban():
    """Un IBAN contient des blocs de 16 chiffres : la detection la plus longue doit gagner."""
    trouve = cats("Compte ZZ06 0000 0000 0000 0000 0000 789 a creancier.")
    assert ("IBAN", "ZZ06 0000 0000 0000 0000 0000 789") in trouve
    assert not any(c == "CARTE_BANCAIRE" for c, _ in trouve)


def test_ip_et_plaque():
    assert ("IP", "192.168.14.27") in cats("serveur 192.168.14.27")
    # une IP en fin de phrase reste detectee malgre le point final
    assert ("IP", "192.168.14.27") in cats("le serveur est en 192.168.14.27. Pensez-y.")
    assert ("IP", "10.42.7.118") in cats("acces 10.42.7.118, journalise")
    # mais un cinquieme groupe de chiffres n'est pas une adresse IP
    assert not any(c == "IP" for c, _ in cats("reference 1.2.3.4.5 du catalogue"))
    assert not any(c == "IP" for c, _ in cats("version 999.1.1.1"))
    assert ("PLAQUE", "EJ-482-QR") in cats("vehicule EJ-482-QR gare")


def test_date_de_naissance_seulement_en_contexte():
    assert ("DATE_NAISSANCE", "14 mars 1991") in cats("nee le 14 mars 1991 a Nullepart")
    assert ("DATE_NAISSANCE", "3 août 1987") in cats("Né le 3 août 1987.")
    assert ("DATE_NAISSANCE", "12/11/1985") in cats("Date de naissance : 12/11/1985")
    # une date de reunion n'est pas une date de naissance
    assert not any(c == "DATE_NAISSANCE" for c, _ in cats("Rendez-vous le 5 février 2026."))


def test_code_postal_ville():
    assert ("CODE_POSTAL_VILLE", "00200 Autrepart") in cats("domicilie a 00200 Autrepart, puis")
    assert ("CODE_POSTAL_VILLE", "00700 Le Hameau") in cats("a 00700 Le Hameau.")
    # le motif ne doit pas deborder sur le mot suivant apres une virgule
    assert ("CODE_POSTAL_VILLE", "00100 Nullepart") in cats("a 00100 Nullepart, SIRET 13002526500013")


def test_aucune_detection_sur_texte_neutre():
    texte = ("Le compte rendu de la reunion de mardi sera diffuse avant la fin "
             "de la semaine. Merci de relire la partie budget.")
    assert cats(texte) == set()
