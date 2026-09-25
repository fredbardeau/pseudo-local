"""Cles de controle des identifiants francais.

Chaque fonction repond a une seule question : cette suite de caracteres est-elle
un identifiant arithmetiquement valide ? C'est ce qui separe un vrai IBAN d'une
suite de chiffres qui lui ressemble.
"""

import re


def _chiffres(valeur: str) -> str:
    return re.sub(r"\D", "", valeur)


def luhn_valide(numero: str) -> bool:
    """Algorithme de Luhn : SIREN, SIRET, cartes de paiement."""
    chiffres = _chiffres(numero)
    if len(chiffres) < 2:
        return False
    total = 0
    for i, c in enumerate(reversed(chiffres)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def siren_valide(numero: str) -> bool:
    return len(_chiffres(numero)) == 9 and luhn_valide(numero)


def siret_valide(numero: str) -> bool:
    chiffres = _chiffres(numero)
    if len(chiffres) != 14:
        return False
    if chiffres.startswith("356000000"):
        # La Poste : exception historique, la somme des chiffres doit etre un multiple de 5.
        return sum(int(c) for c in chiffres) % 5 == 0
    return luhn_valide(chiffres)


def carte_valide(numero: str) -> bool:
    chiffres = _chiffres(numero)
    return len(chiffres) in (13, 14, 15, 16, 17, 18, 19) and luhn_valide(chiffres)


def iban_valide(iban: str) -> bool:
    """Cle IBAN internationale : mod 97 == 1 apres permutation des quatre premiers caracteres."""
    brut = re.sub(r"[^A-Za-z0-9]", "", iban).upper()
    if not (15 <= len(brut) <= 34) or not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", brut):
        return False
    permute = brut[4:] + brut[:4]
    try:
        entier = int("".join(str(int(c, 36)) for c in permute))
    except ValueError:
        return False
    return entier % 97 == 1


def nir_valide(nir: str) -> bool:
    """Numero de securite sociale : 13 caracteres + cle a 2 chiffres.

    En Corse, le departement s'ecrit 2A ou 2B ; la convention officielle remplace
    alors 2A par 19 et 2B par 18 avant le calcul.
    """
    brut = re.sub(r"[^0-9A-Za-z]", "", nir).upper()
    if len(brut) != 15:
        return False
    corps, cle = brut[:13], brut[13:]
    if not cle.isdigit():
        return False
    corps = corps.replace("2A", "19", 1) if "2A" in corps[5:7] else corps
    corps = corps.replace("2B", "18", 1) if "2B" in corps[5:7] else corps
    if not corps.isdigit():
        return False
    return int(cle) == 97 - int(corps) % 97


def ip_valide(adresse: str) -> bool:
    morceaux = adresse.split(".")
    if len(morceaux) != 4:
        return False
    return all(m.isdigit() and len(m) <= 3 and 0 <= int(m) <= 255 for m in morceaux)
