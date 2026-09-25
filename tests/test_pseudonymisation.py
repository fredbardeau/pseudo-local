"""Donnees FICTIVES."""
from pseudo.entites import Entite, fusionner
from pseudo.pseudonymisation import (
    TableCorrespondance, appliquer, meme_entite,
)
from pseudo.regles import detecter
from pseudo.reinjection import reinjecter


def pseudonymiser(texte):
    return appliquer(texte, fusionner(detecter(texte)))


def test_meme_valeur_meme_code():
    texte = ("Ecrivez a claire.durand@example.org. Je repete : claire.durand@example.org "
             "est la bonne adresse, pas camille.fleury@example.org.")
    sortie, table = pseudonymiser(texte)
    assert sortie.count("[EMAIL_001]") == 2
    assert "[EMAIL_002]" in sortie
    assert len(table.correspondances) == 2


def test_iban_avec_et_sans_espaces_partagent_le_code():
    texte = ("Compte ZZ43 0000 0000 0000 0000 0000 123 ; "
             "rappel : ZZ4300000000000000000000123.")
    sortie, table = pseudonymiser(texte)
    assert sortie.count("[IBAN_001]") == 2
    assert len(table.correspondances) == 1


def test_variantes_de_nom_regroupees():
    assert meme_entite("Mme Durand", "Claire Durand")
    assert meme_entite("C. Durand", "Claire Durand")
    assert meme_entite("Durand Claire", "Claire Durand")
    assert meme_entite("Marie-Ange Delaunay", "Delaunay")
    assert meme_entite("Nguyen Thi Lan", "Lan Nguyen")


def test_personnes_distinctes_non_regroupees():
    assert not meme_entite("Claire Durand", "Camille Fleury")
    assert not meme_entite("Rose", "Marchand")
    assert not meme_entite("Pierre Fictif", "Pierre Marchand")


def test_regroupement_dans_un_document():
    entites = [
        Entite(0, 13, "PERSONNE", "Claire Durand", "modele"),
        Entite(20, 30, "PERSONNE", "Mme Durand", "modele"),
        Entite(40, 54, "PERSONNE", "Camille Fleury", "modele"),
    ]
    texte = "Claire Durand ..... Mme Durand ......... Camille Fleury"
    sortie, table = appliquer(texte, entites)
    assert sortie.count("[PERSONNE_001]") == 2
    assert "[PERSONNE_002]" in sortie
    assert table.valeur("[PERSONNE_001]") == "Claire Durand"  # forme la plus complete


def test_aller_retour_complet():
    """Aller-retour sur les deux sources melangees : regles + une entite de modele."""
    texte = ("Bonjour, le dossier de Claire Durand (claire.durand@example.org, "
             "06 39 98 56 78) est valide. IBAN ZZ4300000000000000000000123.")
    debut = texte.index("Claire Durand")
    nom = Entite(debut, debut + len("Claire Durand"), "PERSONNE", "Claire Durand", "modele", 0.9)
    entites = fusionner(detecter(texte) + [nom])
    sortie, table = appliquer(texte, entites)
    assert "Claire Durand" not in sortie and "06 39 98 56 78" not in sortie
    retour = reinjecter(sortie, table)
    assert retour.texte == texte
    assert retour.remplaces == 4


def test_table_sauvegardee_puis_rechargee(tmp_path):
    texte = "Contact : camille.fleury@example.org au 05 36 49 03 88."
    sortie, table = pseudonymiser(texte)
    chemin = table.enregistrer(tmp_path / "t.correspondances.json")
    assert oct(chemin.stat().st_mode)[-3:] == "600"
    rechargee = TableCorrespondance.charger(chemin)
    assert reinjecter(sortie, rechargee).texte == texte


def test_code_abime_par_le_modele_est_rattrape_et_signale():
    _, table = pseudonymiser("Dossier de claire.durand@example.org.")
    reponse = "Voici la reponse pour [EMAIL_1] et [email 001]."
    resultat = reinjecter(reponse, table)
    assert resultat.remplaces == 2
    assert "claire.durand@example.org" in resultat.texte
    assert any("rattrape" in a.raison for a in resultat.anomalies)


def test_code_inconnu_signale_et_laisse_tel_quel():
    _, table = pseudonymiser("Dossier de claire.durand@example.org.")
    resultat = reinjecter("Reponse sur [PERSONNE_042] et [EMAIL_001].", table)
    assert "[PERSONNE_042]" in resultat.texte
    assert any(a.raison.startswith("code absent") for a in resultat.anomalies)


def test_code_oublie_par_le_modele_signale_sans_alarme():
    """Un code que le modele n'a pas repris est signale, mais pas comme un probleme."""
    _, table = pseudonymiser("Dossier de claire.durand@example.org au 06 39 98 56 78.")
    resultat = reinjecter("Le dossier de [EMAIL_001] avance.", table)
    assert [a.code_trouve for a in resultat.non_mentionnes] == ["[TELEPHONE_001]"]
    assert resultat.sans_probleme, "un code non repris ne doit pas declencher d'alerte"


def test_code_inconnu_compte_comme_a_verifier():
    _, table = pseudonymiser("Dossier de claire.durand@example.org.")
    resultat = reinjecter("Reponse sur [PERSONNE_042] et [EMAIL_001].", table)
    assert not resultat.sans_probleme
    assert len(resultat.a_verifier) == 1
