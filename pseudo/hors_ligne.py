"""Verrou reseau : interdit toute connexion sortante dans le processus.

Les variables d'environnement de Hugging Face suffisent en pratique, mais elles
reposent sur la bonne volonte des bibliotheques. Ce verrou-ci est verifiable :
il remplace la fabrique de sockets et fait echouer toute tentative de sortie.

Les connexions vers la machine locale restent autorisees, faute de quoi
l'interface web ne pourrait pas s'ouvrir.
"""

import ipaddress
import socket

HOTES_AUTORISES = {"localhost", "localhost.localdomain", "ip6-localhost", ""}

_socket_origine = socket.socket
_getaddrinfo_origine = socket.getaddrinfo
_actif = False


class SortieReseauInterdite(RuntimeError):
    """Levee quand du code tente une connexion vers l'exterieur."""


def _est_local(hote) -> bool:
    if hote is None:
        return True
    if isinstance(hote, bytes):
        hote = hote.decode("utf-8", "replace")
    if not isinstance(hote, str):
        return False
    if hote in HOTES_AUTORISES:
        return True
    try:
        return ipaddress.ip_address(hote).is_loopback or ipaddress.ip_address(hote).is_unspecified
    except ValueError:
        return False


def _verifier(adresse) -> None:
    hote = adresse[0] if isinstance(adresse, (tuple, list)) and adresse else adresse
    if not _est_local(hote):
        raise SortieReseauInterdite(
            f"Connexion sortante refusee vers {hote!r}. pseudo-local fonctionne "
            f"hors ligne : aucun texte ne doit quitter cette machine."
        )


class _SocketVerrouille(_socket_origine):
    def connect(self, adresse):
        _verifier(adresse)
        return super().connect(adresse)

    def connect_ex(self, adresse):
        _verifier(adresse)
        return super().connect_ex(adresse)

    def sendto(self, donnees, *args):
        if args:
            _verifier(args[-1])
        return super().sendto(donnees, *args)


def _getaddrinfo_verrouille(hote, port, *args, **kwargs):
    _verifier(hote)
    return _getaddrinfo_origine(hote, port, *args, **kwargs)


def verrouiller() -> None:
    """Active le verrou. Idempotent."""
    global _actif
    if _actif:
        return
    socket.socket = _SocketVerrouille
    socket.getaddrinfo = _getaddrinfo_verrouille
    _actif = True


def deverrouiller() -> None:
    """Retablit l'etat d'origine. Utile uniquement dans les tests."""
    global _actif
    socket.socket = _socket_origine
    socket.getaddrinfo = _getaddrinfo_origine
    _actif = False


def est_actif() -> bool:
    return _actif
