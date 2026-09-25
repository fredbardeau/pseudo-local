"""Test de NON-REGRESSION des references de dossier (evaluation/references_neuves/cas.json).

Ce n'est pas une mesure de performance. Les pieges ont ete ecrits avant que la
regle du niveau 2 soit resserree pour les faire passer : les chiffres de ce jeu
sont un plafond. Seuls des documents reels annotes a la main sont probants.

Une reference compte comme masquee si 100 % de ses caracteres sont couverts par
une seule detection (un seul code). Sur les pieges, seule une detection
IDENTIFIANT est un faux positif.
"""

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).parent
sys.path.insert(0, str(RACINE.parent))

from evaluation.commun import verdict  # noqa: E402
from pseudo.pipeline import analyser  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sans-modele", action="store_true", help="regles seules")
    a = p.parse_args()

    cas = json.loads((RACINE / "references_neuves" / "cas.json").read_text(encoding="utf-8"))
    avec_modele = not a.sans_modele

    print(f"\nREFERENCES - NON-REGRESSION (pas une mesure de performance) - "
          f"{'regles + modele' if avec_modele else 'regles seules'}")
    for groupe in ("annoncees", "typees", "nues"):
        total = reussies = 0
        echecs = []
        signalees = 0
        for c in cas[groupe]:
            analyse = analyser(c["phrase"], avec_modele=avec_modele)
            for reference in c["references"]:
                total += 1
                ok, motif = verdict(c["phrase"], reference, analyse.entites)
                debut = c["phrase"].index(reference)
                signalee = any(s.debut <= debut and debut + len(reference) <= s.fin
                               for s in analyse.signalements)
                if ok:
                    reussies += 1
                elif signalee:
                    signalees += 1
                else:
                    echecs.append((c["id"], reference, motif or "non masquee"))
        print(f"\n{groupe:10} {reussies}/{total} masquees entierement, "
              f"{signalees} signalee(s) sans masquage")
        for identifiant, reference, motif in echecs:
            print(f"  ECHEC {identifiant}  {motif:28} {reference!r}")

    faux = []
    for c in cas["pieges"]:
        for e in analyser(c["phrase"], avec_modele=avec_modele).entites:
            if e.categorie == "IDENTIFIANT":
                faux.append((c["id"], e.texte))
    print(f"\npieges     {len(faux)} masque(s) a tort sur {len(cas['pieges'])} phrases")
    for identifiant, texte in faux:
        print(f"  FAUX  {identifiant}  {texte!r}")
    print("\nRappel : seule une mesure sur des documents reels annotes a la main est probante.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
