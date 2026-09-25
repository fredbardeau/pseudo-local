"""pseudo-local : pseudonymisation de textes francais, hors ligne.

Importer ce paquet met le processus en mode hors ligne pour Hugging Face et
pointe le cache de modeles vers ./modeles/. Aucun telechargement ne peut donc
se declencher a l'insu de l'utilisateur ; seul installer_modele.py, qui
n'importe pas ce paquet, a le droit d'aller sur le reseau.
"""

import os
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parent.parent
CACHE_MODELES = RACINE_PROJET / "modeles"

os.environ.setdefault("HF_HOME", str(CACHE_MODELES))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
# Telemetrie desactivee par precaution, meme si le mode hors ligne la neutralise deja.
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

__all__ = ["RACINE_PROJET", "CACHE_MODELES"]
