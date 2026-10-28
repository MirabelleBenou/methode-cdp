"""Le réseau, en sortie seulement : lecture de l'URL de santé et téléchargements HTTPS.

Les sources de téléchargement sont analysées par ``analyser_source`` (dépôts publics et hôtes autorisés de la
configuration, HTTPS seulement). Les redirections ne sont suivies que vers les hôtes permis.
"""

import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from collections import namedtuple

from . import zones

Source = namedtuple("Source", "url hotes_ok")

HOTES_RELEASES = ("objects.githubusercontent.com", "release-assets.githubusercontent.com")
HOTE_GITHUB = "github.com"
MAX_REDIRECTIONS = 5

_RE_GH = re.compile(r"^github:([A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*)@([0-9a-f]{40}):(.+)$")


class ErreurReseau(Exception):
    pass


class ErreurSource(ValueError):
    pass


def _url_https_nette(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https":
        raise ErreurSource("seul HTTPS est permis : %s" % url)
    if not p.hostname or p.username is not None or p.password is not None:
        raise ErreurSource("adresse sans identifiants attendue : %s" % url)
    try:
        port = p.port
    except ValueError:
        raise ErreurSource("port invalide : %s" % url)
    if port not in (None, 443):
        raise ErreurSource("port non permis : %s" % url)
    return p


def hotes_permis(cfg):
    return {HOTE_GITHUB, cfg.hote_fichiers_bruts.lower()} | set(cfg.hotes_autorises)


def analyser_source(source, cfg):
    """Valide une source de ``telecharger`` ; retourne une ``Source`` (URL, hôtes de redirection permis)."""
    if not isinstance(source, str) or not source or "\0" in source or re.search(r"\s", source):
        raise ErreurSource("source invalide")
    m = _RE_GH.match(source)
    if m:
        depot, sha, chemin = m.groups()
        if depot.lower() not in cfg.depots_publics:
            raise ErreurSource("dépôt non autorisé : %s" % depot)
        try:
            chemin = zones.valider_relatif(chemin)
        except zones.ErreurChemin as e:
            raise ErreurSource("chemin de source invalide : %s" % e)
        url = "https://%s/%s/%s/%s" % (cfg.hote_fichiers_bruts, depot, sha, urllib.parse.quote(chemin))
        return Source(url, hotes_permis(cfg))
    if source.startswith("https://") or source.startswith("http://"):
        p = _url_https_nette(source)
        hote = p.hostname.lower()
        if hote == HOTE_GITHUB:
            morceaux = [x for x in p.path.split("/") if x]
            if len(morceaux) >= 6 and morceaux[2] == "releases" and morceaux[3] == "download":
                depot = "%s/%s" % (morceaux[0], morceaux[1])
                if depot.lower() in cfg.depots_publics and ".." not in morceaux:
                    return Source(source, hotes_permis(cfg) | set(HOTES_RELEASES))
            if hote not in cfg.hotes_autorises:
                raise ErreurSource("source github.com non autorisée : %s" % source)
        if hote not in cfg.hotes_autorises:
            raise ErreurSource("hôte non autorisé : %s" % hote)
        if ".." in p.path.split("/"):
            raise ErreurSource("composant '..' refusé dans l'adresse")
        return Source(source, hotes_permis(cfg))
    raise ErreurSource("forme de source inconnue : %s" % source)


# ----------------------------------------------------------------------------------------------
# Transport (remplaçable par les tests)
# ----------------------------------------------------------------------------------------------

class _SansRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _requete(url, delai):
    """Retourne (code, en-têtes, flux) sans suivre les redirections."""
    ouvreur = urllib.request.build_opener(_SansRedirection())
    req = urllib.request.Request(url, headers={"User-Agent": "deployeur"})
    try:
        r = ouvreur.open(req, timeout=delai)
        return r.status, r.headers, r
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, e.headers, e
        raise ErreurReseau("réponse HTTP %s pour %s" % (e.code, url))
    except (urllib.error.URLError, OSError) as e:
        raise ErreurReseau("connexion impossible (%s) : %s" % (url, e))


def telecharger(url, hotes_ok, destination, sha256=None, taille_max=None, place_min_octets=0, battement=None,
                delai=60):
    """Télécharge ``url`` (HTTPS) dans ``destination`` (fichier ``.part`` choisi par l'appelant).

    Retourne (taille, sha256). Lève ErreurReseau (hôte, redirection, taille, place, sha256).
    """
    courant = url
    for _ in range(MAX_REDIRECTIONS + 1):
        p = _url_https_nette(courant)
        if p.hostname.lower() not in hotes_ok:
            raise ErreurReseau("hôte non permis : %s" % p.hostname)
        code, entetes, flux = _requete(courant, delai)
        if 300 <= code < 400:
            suite = entetes.get("Location")
            try:
                flux.close()
            except Exception:
                pass
            if not suite:
                raise ErreurReseau("redirection sans destination")
            courant = urllib.parse.urljoin(courant, suite)
            continue
        break
    else:
        raise ErreurReseau("trop de redirections")
    dossier = os.path.dirname(destination)
    h = hashlib.sha256()
    total = 0
    try:
        annonce = entetes.get("Content-Length")
        if annonce and annonce.isdigit():
            if taille_max is not None and int(annonce) > taille_max:
                raise ErreurReseau("fichier trop gros (%s octets annoncés)" % annonce)
            if shutil.disk_usage(dossier).free - int(annonce) < place_min_octets:
                raise ErreurReseau("place insuffisante pour %s octets" % annonce)
        with open(destination, "wb") as f:
            while True:
                bloc = flux.read(1 << 20)
                if not bloc:
                    break
                f.write(bloc)
                h.update(bloc)
                total += len(bloc)
                if taille_max is not None and total > taille_max:
                    raise ErreurReseau("fichier trop gros (plus de %d octets)" % taille_max)
                if total % (16 << 20) < (1 << 20) and shutil.disk_usage(dossier).free < place_min_octets:
                    raise ErreurReseau("place insuffisante pendant le téléchargement")
                if battement:
                    battement()
            f.flush()
            os.fsync(f.fileno())
    except (OSError, ValueError) as e:
        raise ErreurReseau("lecture interrompue : %s" % e)
    finally:
        try:
            flux.close()
        except Exception:
            pass
    somme = h.hexdigest()
    if sha256 and somme != sha256:
        raise ErreurReseau("sha256 différent de l'attendu (reçu %s)" % somme)
    return total, somme


# ----------------------------------------------------------------------------------------------
# Santé de l'application
# ----------------------------------------------------------------------------------------------

def lire_json(url, delai=5):
    """GET de l'URL de santé ; retourne (objet JSON ou None, erreur ou None)."""
    try:
        ouvreur = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with ouvreur.open(urllib.request.Request(url, headers={"User-Agent": "deployeur"}), timeout=delai) as r:
            donnees = r.read(1 << 20)
        return json.loads(donnees.decode("utf-8")), None
    except (urllib.error.URLError, OSError, ValueError) as e:
        return None, str(e)
