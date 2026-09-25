"""Representation d'une donnee personnelle reperee dans un texte, et arbitrage
entre detections concurrentes."""

from dataclasses import dataclass

#: Ordre de confiance quand deux detections de meme longueur se chevauchent.
PRIORITE_SOURCE = {"humain": 4, "regle": 3, "propagation": 2, "modele": 1,
                   "signalement": 0}


@dataclass(frozen=True)
class Entite:
    debut: int
    fin: int
    categorie: str
    texte: str
    source: str  # "regle", "modele", "propagation", "humain" ou "signalement"
    score: float = 1.0

    @property
    def longueur(self) -> int:
        return self.fin - self.debut

    def chevauche(self, autre: "Entite") -> bool:
        return self.debut < autre.fin and autre.debut < self.fin


def fusionner(entites: list[Entite]) -> list[Entite]:
    """Resout les chevauchements : le span le plus LONG l'emporte.

    C'est un choix oriente masquage : mieux vaut caviarder « 12 rue de l'Exemple,
    00100 Nullepart » en entier que seulement « 00100 Nullepart ». A longueur
    egale, une regle a cle de controle prime sur le modele, qui prime sur rien.
    """
    ordre = sorted(
        entites,
        key=lambda e: (-e.longueur, -PRIORITE_SOURCE[e.source], -e.score, e.debut),
    )
    retenues: list[Entite] = []
    for e in ordre:
        if not any(e.chevauche(r) for r in retenues):
            retenues.append(e)
    return sorted(retenues, key=lambda e: e.debut)
