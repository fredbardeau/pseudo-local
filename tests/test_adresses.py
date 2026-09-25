"""Toutes les valeurs sont FICTIVES. Exemples distincts du jeu gele des adresses
(conserve dans le depot prive de mesure), qui sert a la mesure et pas au reglage."""
from pseudo.adresses import assembler
from pseudo.entites import Entite, fusionner
from pseudo.pipeline import analyser
from pseudo.pseudonymisation import appliquer


def adresses(texte):
    return [e.texte for e in analyser(texte, avec_modele=False).entites
            if e.categorie == "ADRESSE"]


def test_bloc_entier_un_seul_code():
    texte = "Ecrire au 9 rue des Cordiers, bâtiment A, 00300 Ville-sur-Rive. Merci."
    assert adresses(texte) == ["9 rue des Cordiers, bâtiment A, 00300 Ville-sur-Rive"]
    sortie, _ = appliquer(texte, analyser(texte, avec_modele=False).entites)
    assert sortie == "Ecrire au [ADRESSE_001]. Merci."


def test_adresse_sur_plusieurs_lignes():
    assert adresses("M. X\n4 allée Racine\n00400 Nullepart\n") == ["4 allée Racine\n00400 Nullepart"]


def test_voie_sans_numero_et_sans_code_postal():
    assert adresses("Rendez-vous place du Marché demain.") == ["place du Marché"]
    assert adresses("Passez au 3 rue Molière avant midi.") == ["3 rue Molière"]


def test_deux_adresses_separees_par_un_mot():
    assert adresses("Au 2 rue Racine ou au 8 rue Corneille.") == ["2 rue Racine", "8 rue Corneille"]


def test_mots_courants_hors_adresse():
    for texte in ["Il attend dans la rue.", "On mangera sur place.",
                  "La place du bénévolat dans le projet.", "Les 4 allées sont propres."]:
        assert adresses(texte) == [], texte


def test_complement_seul_ignore():
    assert adresses("Le bâtiment B ferme tôt. Réunion au 2e étage.") == []


def test_code_postal_seul_garde_sa_categorie():
    entites = analyser("Il vit à 00400 Nullepart.", avec_modele=False).entites
    assert [(e.categorie, e.texte) for e in entites] == [("CODE_POSTAL_VILLE", "00400 Nullepart")]


def test_forme_internationale_et_cedex():
    entites = analyser("Envoi : F-00500 Nullepart Cedex 3.", avec_modele=False).entites
    assert [e.texte for e in entites] == ["F-00500 Nullepart Cedex 3"]


def test_adresse_du_modele_sans_ancrage_ecartee():
    texte = "Rue fermée pour travaux."
    modele = Entite(0, 10, "ADRESSE", "Rue fermée", "modele", 0.6)
    assert assembler(texte, [modele]) == []


def test_adresse_du_modele_prolonge_un_bloc_ancre():
    texte = "Siège : Mairie annexe, 12 rue Hoche, 00600 Autrepart."
    modele = Entite(8, 21, "ADRESSE", "Mairie annexe", "modele", 0.6)
    trouvees = [e for e in analyser(texte, avec_modele=False).entites] + [modele]
    blocs = [e.texte for e in fusionner(assembler(texte, trouvees)) if e.categorie == "ADRESSE"]
    assert blocs == ["Mairie annexe, 12 rue Hoche, 00600 Autrepart"]
