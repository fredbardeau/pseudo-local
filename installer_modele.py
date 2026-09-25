"""Telecharge le modele de detection une seule fois, dans ./modeles/.

C'est le SEUL moment ou pseudo-local utilise le reseau. Une fois ce script
execute, tout le reste fonctionne hors ligne, et le verifie.
"""
import os
import sys
from pathlib import Path

RACINE = Path(__file__).parent
CACHE = RACINE / "modeles"
MODELE = "fastino/gliner2-privacy-filter-PII-multi"


def main() -> int:
    CACHE.mkdir(exist_ok=True)
    os.environ["HF_HOME"] = str(CACHE)
    os.environ.pop("HF_HUB_OFFLINE", None)

    from huggingface_hub import snapshot_download

    print(f"Telechargement de {MODELE} vers {CACHE} ...")
    chemin = snapshot_download(repo_id=MODELE)
    taille = sum(f.stat().st_size for f in CACHE.rglob("*") if f.is_file())
    print(f"\nTelecharge dans : {chemin}")
    print(f"Place occupee   : {taille / 1024**2:.0f} Mo")

    print("\nVerification du chargement hors ligne ...")
    os.environ["HF_HUB_OFFLINE"] = "1"
    from gliner2 import GLiNER2

    modele = GLiNER2.from_pretrained(MODELE)
    essai = modele.extract_entities(
        "Contactez Jeanne Dupont au 06 39 98 22 33.",
        ["person", "phone_number"],
        threshold=0.3,
    )
    print("Sortie d'essai :", essai)
    print("\nInstallation terminee. Vous pouvez couper le reseau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
