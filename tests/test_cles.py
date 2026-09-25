"""Valeurs a cle VALIDE, choisies pour ne pouvoir designer personne.

Une cle fausse ne suffit pas : elle se recalcule a partir du corps du numero.
C'est le corps qui doit etre impossible ou non personnel.
- IBAN : code pays ZZ, code ISO 3166-1 « a usage utilisateur », jamais attribue
  a un pays (Kosovo utilise XK dans les IBAN, d'ou l'absence de X*).
- NIR : lieu de naissance 99 999. Ne a l'etranger, le lieu s'ecrit 99 suivi du
  code Insee du pays :
  https://www.service-public.gouv.fr/particuliers/vosdroits/F33078
  Aucun code pays Insee ne finit par 999, ni en 2026 ni depuis 1943 (codes 99100
  a 99699, fichiers v_pays_territoire_2026.csv et v_pays_et_territoire_depuis_1943.csv) :
  https://www.insee.fr/fr/information/8740222
- SIREN / SIRET : Insee (120027016, siege 12002701600563) et DINUM
  (13002526500013), personnes morales de droit public (nature juridique 7120),
  publiees au repertoire Sirene : pas des donnees personnelles.
- Cartes : Visa 4242 4242 4242 4242 et Mastercard 5555 5555 5555 4444, que Stripe
  documente comme cartes de test (https://docs.stripe.com/testing). Stripe ne dit
  pas qu'ils n'ont jamais ete emis ; on ne l'affirme pas non plus.
"""
import pytest

from pseudo.cles import (
    carte_valide, iban_valide, ip_valide, luhn_valide,
    nir_valide, siren_valide, siret_valide,
)


@pytest.mark.parametrize("iban", [
    "ZZ4300000000000000000000123",
    "ZZ43 0000 0000 0000 0000 0000 123",
    "zz43 0000 0000 0000 0000 0000 123",
    "ZZ7300000000000000000000456",
    "ZZ0600000000000000000000789",
    "ZZ2600000000000000000001011",
])
def test_iban_valide(iban):
    assert iban_valide(iban)


@pytest.mark.parametrize("iban", [
    "ZZ4300000000000000000000124",   # dernier chiffre modifie
    "ZZ4200000000000000000000123",   # cle de controle modifiee
    "ZZ430000000000000000000012",    # un chiffre en moins
    "",
    "PAS UN IBAN",
])
def test_iban_invalide(iban):
    assert not iban_valide(iban)


@pytest.mark.parametrize("nir", [
    "2780599999042 42", "1 87 08 99 999 318 05",
    "1651199999318 64", "2 91 03 99 999 007 87",
])
def test_nir_valide(nir):
    assert nir_valide(nir)


@pytest.mark.parametrize("nir", [
    "2780599999042 43",     # cle fausse
    "2780599999043 42",     # corps modifie
    "278059999904242123",   # trop long
    "1 87 08 99 999 318",   # cle absente
])
def test_nir_invalide(nir):
    assert not nir_valide(nir)


def test_siren_et_siret():
    assert siren_valide("120027016")
    assert not siren_valide("120027017")
    assert not siren_valide("1200270160")       # bonne longueur exigee
    assert siret_valide("12002701600563")
    assert siret_valide("13002526500013")
    assert not siret_valide("12002701600564")
    assert not siret_valide("120027016")        # un SIREN n'est pas un SIRET


def test_carte():
    assert carte_valide("4242424242424242")
    assert carte_valide("4242 4242 4242 4242")
    assert carte_valide("5555555555554444")
    assert not carte_valide("4242424242424243")
    assert not luhn_valide("1")


def test_ip():
    assert ip_valide("192.168.14.27")
    assert ip_valide("10.42.7.118")
    assert not ip_valide("999.1.1.1")
    assert not ip_valide("1.2.3")


def test_faux_positif_courant():
    """Une suite de chiffres quelconque ne doit pas passer pour un identifiant."""
    assert not siret_valide("12345678901234")
    assert not nir_valide("199999999999999")
