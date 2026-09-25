"""Mesure du rappel et de la precision sur le corpus de test fige.

Trois chiffres par categorie, parce qu'ils ne disent pas la meme chose :

  rappel de masquage : la donnee attendue est-elle caviardee, peu importe
      l'etiquette posee ? C'est ce qui compte pour ne pas fuiter.
  rappel type        : idem, et avec la bonne categorie. C'est ce qui compte
      pour la lisibilite du texte pseudonymise.
  precision          : parmi ce que l'outil a caviarde, quelle part etait
      effectivement une donnee personnelle ?

Une donnee attendue est consideree comme masquee si au moins 80 % de ses
caracteres sont couverts par une ou plusieurs detections.

La colonne « Entier » applique la regle du tout ou rien : 100 % des caracteres
couverts, par une seule detection (un seul code). C'est le critere des adresses.
"""

import argparse
import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).parent
sys.path.insert(0, str(RACINE.parent))

from pseudo.pipeline import analyser                      # noqa: E402
from evaluation.verifier_corpus import spans_attendus     # noqa: E402

COUVERTURE_MINIMALE = 0.80

CRITERES = {
    "identifiants a format fixe": (
        ["IBAN", "NIR", "EMAIL", "TELEPHONE", "SIRET", "SIREN", "CARTE_BANCAIRE"],
        1.00,
    ),
    "noms de personnes": (["PERSONNE"], 0.90),
}


def couverture(debut: int, fin: int, predits: list[tuple[int, int]]) -> float:
    if fin <= debut:
        return 0.0
    couvert = set()
    for pd, pf in predits:
        couvert |= set(range(max(pd, debut), min(pf, fin)))
    return len(couvert) / (fin - debut)


def evaluer(avec_modele: bool, seuil: float, bavard: bool) -> dict:
    verite = json.loads((RACINE / "verite_terrain.json").read_text(encoding="utf-8"))
    documents = verite["documents"]

    stats: dict[str, dict[str, int]] = {}
    oublis: list[tuple[str, str, str]] = []
    non_entieres: list[tuple[str, str, str, float, int]] = []
    faux_positifs: list[tuple[str, str, str]] = []
    indirects_total = indirects_touches = 0
    signalements = 0
    total_predits = total_justes = 0
    debut_chrono = time.perf_counter()
    caracteres = 0

    for nom in sorted(documents):
        texte = (RACINE / "corpus" / nom).read_text(encoding="utf-8")
        caracteres += len(texte)
        attendus = spans_attendus(texte, documents[nom])
        analyse = analyser(texte, seuil=seuil, avec_modele=avec_modele)
        predits = [(e.debut, e.fin, e.categorie) for e in analyse.entites]
        signalements += len(analyse.signalements)
        positions = [(d, f) for d, f, _ in predits]

        for debut, fin, categorie in attendus:
            s = stats.setdefault(categorie,
                                 {"attendus": 0, "masques": 0, "types": 0, "entiers": 0})
            s["attendus"] += 1
            taux = couverture(debut, fin, positions)
            couvrantes = [1 for pd, pf in positions if pd < fin and debut < pf]
            if taux >= 1.0 and len(couvrantes) == 1:
                s["entiers"] += 1
            elif categorie in ("ADRESSE", "CODE_POSTAL_VILLE"):
                non_entieres.append((nom, categorie, texte[debut:fin], taux, len(couvrantes)))
            if taux >= COUVERTURE_MINIMALE:
                s["masques"] += 1
                if any(pc == categorie and pd < fin and debut < pf
                       for pd, pf, pc in predits):
                    s["types"] += 1
            else:
                oublis.append((nom, categorie, texte[debut:fin], taux))

        for pd, pf, pc in predits:
            total_predits += 1
            if any(pd < f and d < pf for d, f, _ in attendus):
                total_justes += 1
            else:
                faux_positifs.append((nom, pc, texte[pd:pf]))

        for phrase in documents[nom]["indirects"]:
            indirects_total += 1
            d = texte.index(phrase)
            if couverture(d, d + len(phrase), positions) >= COUVERTURE_MINIMALE:
                indirects_touches += 1

    duree = time.perf_counter() - debut_chrono
    return {
        "stats": stats, "oublis": oublis, "faux_positifs": faux_positifs,
        "non_entieres": non_entieres, "signalements": signalements,
        "total_predits": total_predits, "total_justes": total_justes,
        "indirects_total": indirects_total, "indirects_touches": indirects_touches,
        "duree": duree, "caracteres": caracteres, "bavard": bavard,
    }


def afficher(r: dict, avec_modele: bool, seuil: float) -> bool:
    stats, faux_positifs = r["stats"], r["faux_positifs"]
    fp_par_categorie: dict[str, int] = {}
    for _, categorie, _ in faux_positifs:
        fp_par_categorie[categorie] = fp_par_categorie.get(categorie, 0) + 1
    predits_par_categorie: dict[str, int] = {}
    for categorie, s in stats.items():
        predits_par_categorie[categorie] = s["masques"]

    mode = f"regles + modele (seuil {seuil})" if avec_modele else "regles seules"
    print(f"\n{'=' * 78}\nEVALUATION - {mode}\n{'=' * 78}")
    print(f"{'Categorie':20} {'Attendus':>8} {'Masques':>8} {'Rappel':>8} "
          f"{'Type':>8} {'Entier':>8} {'Faux pos.':>10}")
    print("-" * 78)

    for categorie in sorted(stats):
        s = stats[categorie]
        rappel = s["masques"] / s["attendus"]
        typee = s["types"] / s["attendus"]
        entier = s["entiers"] / s["attendus"]
        print(f"{categorie:20} {s['attendus']:>8} {s['masques']:>8} {rappel:>7.0%} "
              f"{typee:>7.0%} {entier:>7.0%} {fp_par_categorie.get(categorie, 0):>10}")

    total_attendus = sum(s["attendus"] for s in stats.values())
    total_masques = sum(s["masques"] for s in stats.values())
    precision = r["total_justes"] / r["total_predits"] if r["total_predits"] else 0.0
    print("-" * 78)
    print(f"{'ENSEMBLE':20} {total_attendus:>8} {total_masques:>8} "
          f"{total_masques / total_attendus:>7.0%} {'':>8} {'':>8} {len(faux_positifs):>10}")
    print(f"\nPrecision globale : {precision:.0%} "
          f"({r['total_justes']} detections utiles sur {r['total_predits']})")
    print(f"Duree             : {r['duree']:.1f} s pour {r['caracteres']} caracteres "
          f"({r['caracteres'] / max(r['duree'], 1e-9):.0f} car/s)")

    print(f"Signalements      : {r['signalements']} reference(s) possible(s), "
          f"laissee(s) en clair pour la relecture (non comptees ci-dessus)")

    print(f"\n{'-' * 78}\nCRITERES DECIDES A L'AVANCE\n{'-' * 78}")
    tout_tenu = True
    for libelle, (categories, cible) in CRITERES.items():
        attendus = sum(stats.get(c, {}).get("attendus", 0) for c in categories)
        masques = sum(stats.get(c, {}).get("masques", 0) for c in categories)
        obtenu = masques / attendus if attendus else 0.0
        tenu = obtenu >= cible
        tout_tenu &= tenu
        print(f"  {'ATTEINT' if tenu else 'NON ATTEINT':12} {libelle:30} "
              f"cible {cible:.0%}  obtenu {obtenu:.0%}  ({masques}/{attendus})")

    print(f"\n{'-' * 78}\nIDENTIFIANTS INDIRECTS (non detectes par conception)\n{'-' * 78}")
    print(f"  {r['indirects_touches']} sur {r['indirects_total']} formulations indirectes "
          f"sont couvertes par une detection.")
    print("  Les autres passent entre les mailles : c'est precisement ce que la")
    print("  relecture humaine doit rattraper.")

    if r["oublis"]:
        print(f"\n{'-' * 78}\nDONNEES NON MASQUEES ({len(r['oublis'])})\n{'-' * 78}")
        print("  (« couvert » = part des caracteres tout de meme masquee ;")
        print("   30 % sur une adresse veut dire que le code postal est masque mais pas la rue)")
        for nom, categorie, extrait, taux in sorted(r["oublis"], key=lambda o: -o[3]):
            print(f"  couvert {taux:>4.0%}  {nom:26} {categorie:18} {extrait!r}")

    if r["non_entieres"]:
        print(f"\n{'-' * 78}\nADRESSES NON MASQUEES ENTIEREMENT ({len(r['non_entieres'])})\n{'-' * 78}")
        for nom, categorie, extrait, taux, codes in r["non_entieres"]:
            print(f"  couvert {taux:>4.0%} en {codes} code(s)  {nom:26} {categorie:18} {extrait!r}")

    if r["bavard"] and faux_positifs:
        print(f"\n{'-' * 78}\nFAUX POSITIFS ({len(faux_positifs)})\n{'-' * 78}")
        for nom, categorie, extrait in faux_positifs:
            print(f"  {nom:26} {categorie:18} {extrait!r}")

    return tout_tenu


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sans-modele", action="store_true",
                   help="n'evaluer que la couche 1 (regles deterministes)")
    p.add_argument("--seuil", type=float, default=0.4,
                   help="seuil de confiance du modele (defaut : 0.4)")
    p.add_argument("--faux-positifs", action="store_true",
                   help="lister le detail des faux positifs")
    a = p.parse_args()

    if not (RACINE / "verite_terrain.json").exists() or not any((RACINE / "corpus").glob("*.txt")):
        print("Corpus de test absent : evaluation/corpus/ et evaluation/verite_terrain.json.\n"
              "Ce corpus reste prive : il contient des identifiants a cle valide dont on ne peut\n"
              "garantir qu'ils ne designent personne. La mesure ne se rejoue qu'avec lui.\n"
              "Ses empreintes sont dans evaluation/EMPREINTES.txt. Pour essayer l'outil : demo/.",
              file=sys.stderr)
        return 2
    r = evaluer(avec_modele=not a.sans_modele, seuil=a.seuil, bavard=a.faux_positifs)
    return 0 if afficher(r, not a.sans_modele, a.seuil) else 1


if __name__ == "__main__":
    sys.exit(main())
