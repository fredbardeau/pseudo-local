"""Couche 4 : relecture humaine, dans le navigateur, en local uniquement.

L'interface n'est jamais un simple afficheur : elle existe parce que la
detection automatique est incomplete par nature. Le bandeau d'avertissement
est permanent, et non repliable, pour cette raison.
"""

import json
from datetime import datetime
from pathlib import Path

import gradio as gr

from . import RACINE_PROJET, hors_ligne
from .entites import Entite, fusionner
from .fichiers import FormatNonSupporte, PdfSansTexte, lire
from .modele import SEUIL_DEFAUT
from .pipeline import analyser, propager
from .pseudonymisation import TableCorrespondance, appliquer
from .reinjection import reinjecter

SORTIES = RACINE_PROJET / "sorties"

CATEGORIES = [
    "PERSONNE", "ADRESSE", "ORGANISATION", "LIEU", "EMAIL", "TELEPHONE",
    "IBAN", "NIR", "SIREN", "SIRET", "CARTE_BANCAIRE", "IP", "PLAQUE",
    "DATE_NAISSANCE", "CODE_POSTAL_VILLE", "IDENTIFIANT",
]

COULEURS = {
    "PERSONNE": "#c62828", "ADRESSE": "#ad1457", "ORGANISATION": "#6a1b9a",
    "LIEU": "#4527a0", "EMAIL": "#1565c0", "TELEPHONE": "#00838f",
    "IBAN": "#00695c", "NIR": "#2e7d32", "SIREN": "#558b2f", "SIRET": "#558b2f",
    "CARTE_BANCAIRE": "#ef6c00", "IP": "#4e342e", "PLAQUE": "#37474f",
    "DATE_NAISSANCE": "#d84315", "CODE_POSTAL_VILLE": "#0277bd",
    "IDENTIFIANT": "#795548",
}

BANDEAU = """
# pseudo-local

<div style="background:#7f1d1d;color:#fff;padding:14px 18px;border-radius:8px;
            font-size:15px;line-height:1.5">
<b>Les noms indirects ne sont PAS détectés automatiquement : relisez.</b><br>
Une fonction plus un lieu (« la directrice de l'antenne de [VILLE] »), un détail
de santé, une situation familiale (« la maman des triplés »), un signe distinctif
(« le seul éducateur homme de l'équipe ») identifient une personne aussi sûrement
qu'un nom — et aucun modèle ne les repère. C'est à vous de les voir.
</div>

<div style="background:#78350f;color:#fff;padding:12px 18px;border-radius:8px;
            margin-top:8px;font-size:14px;line-height:1.5">
Ceci est une <b>pseudonymisation</b> au sens du RGPD, pas une anonymisation.
Tant que la table de correspondance existe, le texte produit reste une donnée
à caractère personnel. Protégez la table comme le document d'origine.
</div>
"""


# --- rendu ---

def _surligner(texte: str, entites: list[Entite]) -> list[tuple[str, str | None]]:
    morceaux, curseur = [], 0
    for e in sorted(entites, key=lambda e: e.debut):
        if e.debut > curseur:
            morceaux.append((texte[curseur:e.debut], None))
        morceaux.append((texte[e.debut:e.fin], e.categorie))
        curseur = e.fin
    morceaux.append((texte[curseur:], None))
    return [m for m in morceaux if m[0]]


#: Seules ces categories passent par une somme de controle reellement calculee
#: (voir cles.py). Annoncer « cle verifiee » ailleurs inviterait a ne pas relire
#: justement la ou il faut : une adresse ou une reference n'a aucune cle.
CATEGORIES_A_CLE = {"IBAN", "NIR", "SIREN", "SIRET", "CARTE_BANCAIRE"}


def _origine(e: Entite) -> str:
    if e.source == "regle":
        return "clé vérifiée" if e.categorie in CATEGORIES_A_CLE else "format reconnu"
    return {"modele": "modèle", "propagation": "propagé", "humain": "ajouté",
            "signalement": "à trancher"}[e.source]


def _etiquette(e: Entite) -> str:
    return f"{e.categorie} · « {e.texte} » — {_origine(e)} (position {e.debut})"


def _serialiser(entites: list[Entite]) -> list[dict]:
    return [{"debut": e.debut, "fin": e.fin, "categorie": e.categorie,
             "texte": e.texte, "source": e.source, "score": e.score} for e in entites]


def _deserialiser(donnees: list[dict]) -> list[Entite]:
    return [Entite(**d) for d in donnees]


def _rafraichir(texte: str, entites: list[Entite]):
    choix = [_etiquette(e) for e in entites]
    # Un signalement arrive decoche : il reste en clair tant que vous ne le cochez pas.
    cochees = [_etiquette(e) for e in entites if e.source != "signalement"]
    signalements = len(choix) - len(cochees)
    message = (f"{len(cochees)} détection(s). Décochez ce qui n'est pas une donnée personnelle.")
    if signalements:
        message += (f" {signalements} référence(s) possible(s), décochée(s) : "
                    f"cochez celles à masquer.")
    return (
        gr.HighlightedText(value=_surligner(texte, entites)),
        gr.CheckboxGroup(choices=choix, value=cochees),
        _serialiser(entites),
        message,
    )


# --- actions ---

def action_analyser(texte, fichier, seuil):
    if fichier:
        try:
            texte = lire(fichier)
        except (FormatNonSupporte, PdfSansTexte) as erreur:
            return (texte or "", gr.HighlightedText(value=None),
                    gr.CheckboxGroup(choices=[], value=[]), [], f"⚠️ {erreur}")
    if not (texte or "").strip():
        return ("", gr.HighlightedText(value=None),
                gr.CheckboxGroup(choices=[], value=[]), [],
                "Collez un texte ou choisissez un fichier.")

    analyse = analyser(texte, seuil=seuil)
    entites = sorted(analyse.entites + analyse.signalements, key=lambda e: e.debut)
    surligne, cases, etat, message = _rafraichir(texte, entites)
    return texte, surligne, cases, etat, message


def action_ajouter(texte, etat, a_ajouter, categorie):
    entites = _deserialiser(etat)
    a_ajouter = (a_ajouter or "").strip()
    if not a_ajouter:
        return (*_rafraichir(texte, entites)[:3],
                "Indiquez le texte oublié, tel qu'il apparaît dans le document.")
    if a_ajouter not in texte:
        return (*_rafraichir(texte, entites)[:3],
                f"« {a_ajouter} » est introuvable dans le document, au caractère près.")

    ajouts, depart = [], 0
    while (i := texte.find(a_ajouter, depart)) != -1:
        ajouts.append(Entite(i, i + len(a_ajouter), categorie, a_ajouter, "humain"))
        depart = i + len(a_ajouter)
    entites = fusionner(ajouts + entites)
    entites = fusionner(entites + propager(texte, [e for e in ajouts]))
    surligne, cases, nouvel_etat, _ = _rafraichir(texte, entites)
    return surligne, cases, nouvel_etat, f"« {a_ajouter} » ajouté ({len(ajouts)} occurrence(s))."


def action_produire(texte, etat, gardees):
    entites = [e for e in _deserialiser(etat) if _etiquette(e) in set(gardees)]
    if not entites:
        return "", None, None, "Aucune détection retenue : le texte sortirait inchangé."

    sortie, table = appliquer(texte, entites)
    SORTIES.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    chemin = table.enregistrer(SORTIES / f"{horodatage}.correspondances.json")
    ecartees = sum(1 for e in _deserialiser(etat)
                   if e.source != "signalement" and _etiquette(e) not in set(gardees))
    return (sortie, str(chemin), table.en_dictionnaire(),
            f"{len(entites)} donnée(s) remplacée(s), {ecartees} écartée(s) par vous. "
            f"Table enregistrée dans {chemin.name} — protégez-la.")


def action_reinjecter(reponse, fichier_table, table_session):
    if fichier_table:
        donnees = json.loads(Path(fichier_table).read_text(encoding="utf-8"))
    elif table_session:
        donnees = table_session
    else:
        return "", "Choisissez une table de correspondance."
    if not (reponse or "").strip():
        return "", "Collez la réponse du modèle de langage."

    resultat = reinjecter(reponse, TableCorrespondance.depuis_dictionnaire(donnees))
    lignes = [f"{resultat.remplaces} code(s) remplacé(s)."]

    if resultat.a_verifier:
        lignes.append(f"\n⚠️  {len(resultat.a_verifier)} point(s) à vérifier :")
        for a in resultat.a_verifier:
            fin = f" → {a.code_retenu}" if a.code_retenu else ""
            lignes.append(f"  • {a.code_trouve} : {a.raison}{fin}")
    else:
        lignes.append("Aucun code abîmé ni inventé : la réinjection est fidèle.")

    if resultat.non_mentionnes:
        codes = ", ".join(a.code_trouve for a in resultat.non_mentionnes)
        lignes.append(f"\nPour information, {len(resultat.non_mentionnes)} code(s) de la "
                      f"table n'apparaissent pas dans la réponse — normal si le modèle "
                      f"a résumé :\n  {codes}")
    return resultat.texte, "\n".join(lignes)


# --- assemblage ---

def construire() -> gr.Blocks:
    with gr.Blocks(title="pseudo-local") as app:
        gr.Markdown(BANDEAU)
        etat_entites = gr.State([])
        etat_table = gr.State(None)

        with gr.Tab("1 · Pseudonymiser"):
            with gr.Row():
                with gr.Column(scale=3):
                    saisie = gr.Textbox(label="Texte à pseudonymiser", lines=14,
                                        placeholder="Collez ici le texte…")
                with gr.Column(scale=2):
                    fichier = gr.File(label="…ou un fichier (.txt, .md, .docx, .pdf)",
                                      type="filepath",
                                      file_types=[".txt", ".md", ".docx", ".pdf"])
                    seuil = gr.Slider(0.1, 0.9, value=SEUIL_DEFAUT, step=0.05,
                                      label="Seuil du modèle",
                                      info="Plus bas = détecte plus, se trompe plus.")
                    bouton_analyser = gr.Button("Analyser", variant="primary")

            message = gr.Markdown()
            surligne = gr.HighlightedText(label="Détections", color_map=COULEURS,
                                          show_legend=True, combine_adjacent=False)

            with gr.Accordion("Corriger les détections", open=True):
                cases = gr.CheckboxGroup(
                    label="Décochez un faux positif pour le laisser en clair", choices=[])
                with gr.Row():
                    oubli = gr.Textbox(label="Texte oublié à masquer", scale=3,
                                       placeholder="Recopiez-le exactement…")
                    categorie = gr.Dropdown(CATEGORIES, value="PERSONNE",
                                            label="Catégorie", scale=1)
                    bouton_ajouter = gr.Button("Ajouter", scale=1)

            bouton_produire = gr.Button("Produire le texte pseudonymisé",
                                        variant="primary")
            sortie = gr.Textbox(label="Texte pseudonymisé — à coller dans le modèle",
                                lines=14, buttons=["copy"])
            fichier_table = gr.File(label="Table de correspondance (à conserver hors ligne)")

            bouton_analyser.click(
                action_analyser, [saisie, fichier, seuil],
                [saisie, surligne, cases, etat_entites, message])
            bouton_ajouter.click(
                action_ajouter, [saisie, etat_entites, oubli, categorie],
                [surligne, cases, etat_entites, message])
            bouton_produire.click(
                action_produire, [saisie, etat_entites, cases],
                [sortie, fichier_table, etat_table, message])

        with gr.Tab("2 · Réinjecter"):
            gr.Markdown(
                "Collez la réponse du modèle de langage. Les codes seront remplacés "
                "par les vraies valeurs. Les codes que le modèle a modifiés ou inventés "
                "sont signalés plutôt que remplacés en silence.")
            reponse = gr.Textbox(label="Réponse du modèle de langage", lines=12)
            table_importee = gr.File(label="Table de correspondance (.json)",
                                     type="filepath", file_types=[".json"])
            gr.Markdown("*Si vous venez de pseudonymiser dans l'onglet 1, "
                        "la table de cette session est utilisée automatiquement.*")
            bouton_reinjecter = gr.Button("Réinjecter", variant="primary")
            texte_restaure = gr.Textbox(label="Texte avec les vraies valeurs", lines=12,
                                        buttons=["copy"])
            rapport = gr.Textbox(label="Contrôle", lines=6)

            bouton_reinjecter.click(
                action_reinjecter, [reponse, table_importee, etat_table],
                [texte_restaure, rapport])

    return app


def lancer(port: int = 7860, verrou_reseau: bool = True) -> None:
    if verrou_reseau:
        hors_ligne.verrouiller()

    # Chargement du modele AVANT d'ouvrir l'interface. Sans cela il se chargerait
    # au premier clic sur « Analyser », qui semblerait rester bloque une
    # vingtaine de secondes. Mieux vaut attendre pendant que rien n'est affiche.
    import contextlib
    import io

    from .modele import charger

    print("Chargement du modele de detection…", flush=True)
    # GLiNER2 affiche sa configuration technique : sans interet ici, et
    # deroutant pour quelqu'un qui a simplement double-clique sur une icone.
    with contextlib.redirect_stdout(io.StringIO()):
        charger()
    print("Modele pret. Ouverture de l'interface.", flush=True)
    # server_name explicite : jamais 0.0.0.0, l'interface ne doit pas etre
    # joignable depuis le reseau local.
    construire().launch(server_name="127.0.0.1", server_port=port,
                        theme=gr.themes.Soft(), share=False, footer_links=[],
                        inbrowser=True, quiet=True)
