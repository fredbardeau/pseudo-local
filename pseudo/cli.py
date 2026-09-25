"""Ligne de commande. `pseudonymiser` un fichier, ou `reinjecter` une reponse."""

import argparse
import sys
from pathlib import Path

from . import hors_ligne
from .fichiers import FormatNonSupporte, PdfSansTexte, lire
from .modele import SEUIL_DEFAUT
from .pipeline import analyser
from .pseudonymisation import TableCorrespondance, appliquer
from .reinjection import reinjecter


def _pseudonymiser(a) -> int:
    source = Path(a.fichier)
    try:
        texte = lire(source)
    except (FormatNonSupporte, PdfSansTexte) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 2

    analyse = analyser(texte, seuil=a.seuil, avec_modele=not a.sans_modele)
    entites = analyse.entites
    sortie, table = appliquer(texte, entites)

    # La table est ecrite a cote du fichier d'origine, jamais ailleurs.
    chemin_table = source.with_suffix(source.suffix + ".correspondances.json")
    chemin_sortie = source.with_suffix(source.suffix + ".pseudonymise.txt")
    chemin_sortie.write_text(sortie, encoding="utf-8")
    table.enregistrer(chemin_table)

    compte: dict[str, int] = {}
    for e in entites:
        compte[e.categorie] = compte.get(e.categorie, 0) + 1
    # On n'affiche que des comptages : aucun extrait du document ne doit
    # apparaitre dans la console ni dans un journal.
    print(f"{len(entites)} donnee(s) remplacee(s) :")
    for categorie, n in sorted(compte.items()):
        print(f"  {categorie:20} {n}")
    if analyse.signalements:
        # Un compteur seulement : jamais d'extrait dans le Terminal.
        print(f"\n{len(analyse.signalements)} reference(s) possible(s) laissee(s) en clair "
              f"(suites de chiffres) : ouvrez l'interface pour trancher.")
    print(f"\nTexte pseudonymise : {chemin_sortie}")
    print(f"Table (a proteger) : {chemin_table}")
    print("\nRappel : la detection automatique ne voit pas les identifiants indirects")
    print("(fonction + lieu, situation familiale, detail de sante). Relisez avant d'envoyer.")
    return 0


def _reinjecter(a) -> int:
    table = TableCorrespondance.charger(a.table)
    resultat = reinjecter(Path(a.reponse).read_text(encoding="utf-8"), table)
    destination = Path(a.reponse).with_suffix(".reinjecte.txt")
    destination.write_text(resultat.texte, encoding="utf-8")
    print(f"{resultat.remplaces} code(s) remplace(s). Resultat : {destination}")

    if resultat.a_verifier:
        print(f"\n{len(resultat.a_verifier)} point(s) a verifier :")
        for anomalie in resultat.a_verifier:
            fin = f" -> {anomalie.code_retenu}" if anomalie.code_retenu else ""
            print(f"  ! {anomalie.code_trouve} : {anomalie.raison}{fin}")
    else:
        print("Aucun code abime ni invente : la reinjection est fidele.")

    if resultat.non_mentionnes:
        codes = ", ".join(a.code_trouve for a in resultat.non_mentionnes)
        print(f"\nPour information, {len(resultat.non_mentionnes)} code(s) de la table "
              f"n'apparaissent pas dans la reponse (normal si le modele a resume) :")
        print(f"  {codes}")
    return 0


def _interface(a) -> int:
    from .interface import lancer

    lancer(port=a.port, verrou_reseau=not a.sans_verrou)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="pseudo-local",
        description="Pseudonymisation de textes francais, 100 %% en local.")
    p.add_argument("--offline", action="store_true",
                   help="verrouille toute sortie reseau du processus (recommande)")
    sous = p.add_subparsers(dest="commande", required=True)

    a = sous.add_parser("pseudonymiser", help="traiter un fichier")
    a.add_argument("fichier")
    a.add_argument("--seuil", type=float, default=SEUIL_DEFAUT)
    a.add_argument("--sans-modele", action="store_true",
                   help="couche 1 seule : rapide, mais ne voit pas les noms")
    a.set_defaults(fonction=_pseudonymiser)

    b = sous.add_parser("reinjecter", help="remettre les vraies valeurs")
    b.add_argument("reponse", help="fichier contenant la reponse du modele")
    b.add_argument("table", help="fichier .correspondances.json")
    b.set_defaults(fonction=_reinjecter)

    c = sous.add_parser("interface", help="ouvrir l'interface de relecture")
    c.add_argument("--port", type=int, default=7860)
    c.add_argument("--sans-verrou", action="store_true",
                   help="ne pas verrouiller les sockets (deconseille)")
    c.set_defaults(fonction=_interface)

    args = p.parse_args(argv)
    if args.offline:
        hors_ligne.verrouiller()
    return args.fonction(args)


if __name__ == "__main__":
    sys.exit(main())
