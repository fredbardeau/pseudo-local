"""Le test central : l'outil fonctionne-t-il vraiment sans reseau ?

On ne se contente pas de verifier des variables d'environnement : on remplace
la fabrique de sockets, puis on fait tourner la chaine complete, modele compris.
Si le moindre composant essayait de sortir, le test echouerait.
"""
import os
import socket

import pytest

from pseudo import hors_ligne
from pseudo.hors_ligne import SortieReseauInterdite


@pytest.fixture
def reseau_verrouille():
    hors_ligne.verrouiller()
    yield
    hors_ligne.deverrouiller()


def test_variables_d_environnement_hors_ligne():
    """Le simple import du paquet suffit a couper les telechargements."""
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"


def test_sortie_refusee(reseau_verrouille):
    with pytest.raises(SortieReseauInterdite):
        socket.create_connection(("huggingface.co", 443), timeout=2)
    with pytest.raises(SortieReseauInterdite):
        socket.socket().connect(("1.1.1.1", 80))
    with pytest.raises(SortieReseauInterdite):
        socket.getaddrinfo("huggingface.co", 443)


def test_boucle_locale_autorisee(reseau_verrouille):
    """L'interface web doit pouvoir s'ouvrir sur 127.0.0.1."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    client = socket.socket()
    client.connect(s.getsockname())        # ne doit pas lever
    client.close()
    s.close()
    socket.getaddrinfo("localhost", 0)     # ne doit pas lever


def test_regles_sans_reseau(reseau_verrouille):
    from pseudo.regles import detecter

    assert detecter("IBAN ZZ4300000000000000000000123 et 06 39 98 56 78.")


@pytest.mark.lent
def test_chaine_complete_sans_reseau(reseau_verrouille):
    """Chargement du modele ET analyse, avec toute sortie reseau interdite."""
    from pseudo.pipeline import analyser

    texte = ("Note de suivi : madame Claire Durand, 12 rue de l'Exemple, "
             "00100 Nullepart, jointe au 06 39 98 56 78.")
    analyse = analyser(texte)
    categories = {e.categorie for e in analyse.entites}
    assert "PERSONNE" in categories
    assert "TELEPHONE" in categories
    assert hors_ligne.est_actif()
