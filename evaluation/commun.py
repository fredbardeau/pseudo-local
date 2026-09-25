"""Outils partages par les scripts de non-regression."""


def verdict(phrase: str, extrait: str, entites) -> tuple[bool, str]:
    """Regle du tout ou rien : 100 % des caracteres couverts, par une seule detection."""
    debut = phrase.index(extrait)
    fin = debut + len(extrait)
    couvrantes = [e for e in entites if e.debut < fin and debut < e.fin]
    couvert = set()
    for e in couvrantes:
        couvert |= set(range(max(e.debut, debut), min(e.fin, fin)))
    taux = len(couvert) / len(extrait)
    if taux < 1.0:
        return False, f"masquee a {taux:.0%}"
    if len(couvrantes) > 1:
        return False, f"entiere mais en {len(couvrantes)} codes"
    return True, ""
