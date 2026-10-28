"""Le SEUL module qui lance des processus.

Chaque commande externe est une fonction dont la liste d'arguments est construite à partir de
constantes et de valeurs validées (sha de 40 caractères hexadécimaux, noms de la configuration,
chemins déjà résolus dans une zone). Jamais d'interpréteur de commandes, jamais une chaîne d'ordre
passée telle quelle à un processus. Un délai sur chaque appel.

Liste blanche des commandes Docker (et rien d'autre) :
  - docker compose -p P --project-directory D -f D/F : build, up -d --no-deps, ps --format json, logs
  - docker inspect, docker volume inspect
  - docker exec : dump de la base, lecture d'un dump, lecture seule de la base
  - docker run --rm --network none --mount ... : archive des écussons
"""

import os
import re
import subprocess
from collections import namedtuple

DELAI_COURT = 120
DELAI_GIT = 300
DELAI_LONG = 3600
DELAI_BUILD = 1800

Resultat = namedtuple("Resultat", "code sortie erreur")
GitAcces = namedtuple("GitAcces", "cle known_hosts")

_RE_NOM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_RE_SHA = re.compile(r"^[0-9a-f]{40}$")
_RE_IMAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:@-]*$")
_RE_HORO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_RE_BRANCHE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")

# Chaîne constante : les identifiants viennent de l'environnement du conteneur de la base.
_SH_DUMP = 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
_SH_LIRE = 'psql -X -q -A -t -F "|" --set=ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

# Script constant, en lecture seule : révision de migration, puis nombre de lignes de chaque table.
_SQL_LIRE = (
    "BEGIN READ ONLY;\n"
    "SELECT 'R', version_num FROM alembic_version;\n"
    "SELECT 'T', table_name, (xpath('/row/c/text()', query_to_xml("
    "format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text "
    "FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
    "ORDER BY table_name;\n"
    "ROLLBACK;\n"
)


class ErreurCommande(Exception):
    """Une commande a échoué (code de sortie non nul, délai dépassé, programme absent)."""

    def __init__(self, argv, code, erreur):
        self.argv = list(argv)
        self.code = code
        self.erreur = erreur or ""
        resume = " ".join(str(a) for a in self.argv[:5])
        super().__init__("commande en échec (code %s) : %s … %s" % (code, resume, self.erreur.strip()[-400:]))


def _nom(valeur, quoi="nom"):
    if not isinstance(valeur, str) or not _RE_NOM.match(valeur):
        raise ValueError("%s invalide : %r" % (quoi, valeur))
    return valeur


def _sha(valeur):
    if not isinstance(valeur, str) or not _RE_SHA.match(valeur):
        raise ValueError("sha invalide : %r" % (valeur,))
    return valeur


def _absolu(chemin, quoi="chemin"):
    if not isinstance(chemin, str) or not os.path.isabs(chemin) or "\0" in chemin:
        raise ValueError("%s doit être absolu : %r" % (quoi, chemin))
    return chemin


def _branche(valeur):
    if not isinstance(valeur, str) or not _RE_BRANCHE.match(valeur) or ".." in valeur:
        raise ValueError("branche invalide : %r" % (valeur,))
    return valeur


def _lancer(argv, delai, env=None, entree_fichier=None, entree_texte=None, sortie_fichier=None,
            tolerer=False):
    """Lance ``argv`` (une liste) sans interpréteur. Retourne un Resultat ; lève ErreurCommande sinon."""
    for a in argv:
        if not isinstance(a, str) or "\0" in a:
            raise ValueError("argument de commande invalide")
    entree = None
    sortie = subprocess.PIPE
    fi = fo = None
    try:
        if entree_fichier is not None:
            fi = open(entree_fichier, "rb")
            entree = fi
        elif entree_texte is not None:
            entree = None
        else:
            entree = subprocess.DEVNULL
        if sortie_fichier is not None:
            fo = open(sortie_fichier, "wb")
            sortie = fo
        try:
            p = subprocess.run(
                argv, shell=False, stdin=entree,
                input=entree_texte.encode("utf-8") if entree_texte is not None else None,
                stdout=sortie, stderr=subprocess.PIPE, timeout=delai, env=env, check=False,
            )
        except subprocess.TimeoutExpired:
            raise ErreurCommande(argv, -1, "délai dépassé (%s s)" % delai)
        except OSError as e:
            raise ErreurCommande(argv, -2, "lancement impossible : %s" % e)
    finally:
        if fi is not None:
            fi.close()
        if fo is not None:
            fo.close()
    out = p.stdout.decode("utf-8", "replace") if p.stdout is not None else ""
    err = p.stderr.decode("utf-8", "replace") if p.stderr is not None else ""
    if p.returncode != 0 and not tolerer:
        raise ErreurCommande(argv, p.returncode, err or out)
    return Resultat(p.returncode, out, err)


# ----------------------------------------------------------------------------------------------
# Docker Compose
# ----------------------------------------------------------------------------------------------

def _compose(projet, dossier, fichier):
    _nom(projet, "projet")
    _absolu(dossier, "dossier")
    _nom(fichier, "fichier compose")
    return ["docker", "compose", "-p", projet, "--project-directory", dossier, "-f", os.path.join(dossier, fichier)]


def compose_build(projet, dossier, fichier, service):
    _nom(service, "service")
    return _lancer(_compose(projet, dossier, fichier) + ["build", service], DELAI_BUILD)


def compose_up(projet, dossier, fichier, service):
    _nom(service, "service")
    return _lancer(_compose(projet, dossier, fichier) + ["up", "-d", "--no-deps", service], DELAI_BUILD)


def compose_ps(projet, dossier, fichier):
    return _lancer(_compose(projet, dossier, fichier) + ["ps", "--format", "json"], DELAI_COURT).sortie


def compose_logs(projet, dossier, fichier, service, depuis):
    _nom(service, "service")
    if not isinstance(depuis, str) or not _RE_HORO.match(depuis):
        raise ValueError("horodatage invalide : %r" % (depuis,))
    return _lancer(_compose(projet, dossier, fichier) + ["logs", "--no-color", "--since", depuis, service],
                   DELAI_COURT).sortie


# ----------------------------------------------------------------------------------------------
# Docker : inspection et conteneur de la base (lecture seulement)
# ----------------------------------------------------------------------------------------------

def docker_inspect(conteneur):
    return _lancer(["docker", "inspect", _nom(conteneur, "conteneur")], DELAI_COURT).sortie


def docker_volume_inspect(volume):
    return _lancer(["docker", "volume", "inspect", _nom(volume, "volume")], DELAI_COURT).sortie


def base_sauvegarder(conteneur, fichier_sortie):
    """Écrit le dump de la base (format personnalisé) dans ``fichier_sortie``."""
    _lancer(["docker", "exec", _nom(conteneur, "conteneur"), "sh", "-c", _SH_DUMP], DELAI_LONG,
            sortie_fichier=_absolu(fichier_sortie))


def base_lister_dump(conteneur, fichier_dump):
    """Lit un dump sur l'entrée standard et rend sa table des matières (rien n'est restauré)."""
    return _lancer(["docker", "exec", "-i", _nom(conteneur, "conteneur"), "pg_restore", "--list"], DELAI_LONG,
                   entree_fichier=_absolu(fichier_dump)).sortie


def base_lire(conteneur):
    """Révision de migration et nombre de lignes de chaque table, dans une transaction en lecture seule."""
    return _lancer(["docker", "exec", "-i", _nom(conteneur, "conteneur"), "sh", "-c", _SH_LIRE], DELAI_COURT,
                   entree_texte=_SQL_LIRE).sortie


def volume_archiver(image, volume, fichier_sortie):
    """Archive un volume en lecture seule, sans réseau, avec l'image déjà présente."""
    if not isinstance(image, str) or not _RE_IMAGE.match(image):
        raise ValueError("image invalide : %r" % (image,))
    _nom(volume, "volume")
    _lancer(["docker", "run", "--rm", "--network", "none", "--mount",
             "type=volume,src=%s,dst=/source,readonly" % volume, image,
             "tar", "-czf", "-", "-C", "/source", "."], DELAI_LONG, sortie_fichier=_absolu(fichier_sortie))


# ----------------------------------------------------------------------------------------------
# Git
# ----------------------------------------------------------------------------------------------

def _env_git(acces):
    env = dict(os.environ)
    env["GIT_SSH_COMMAND"] = ("ssh -i %s -o IdentitiesOnly=yes -o UserKnownHostsFile=%s "
                              "-o StrictHostKeyChecking=yes" % (acces.cle, acces.known_hosts))
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["LC_ALL"] = "C"
    return env


def git_cloner_ordres(acces, url, dest, branche):
    return _lancer(["git", "clone", "--quiet", "--branch", _branche(branche), "--", url, _absolu(dest)],
                   DELAI_GIT, env=_env_git(acces))


def git_cloner_miroir(acces, url, dest):
    return _lancer(["git", "clone", "--quiet", "--bare", "--", url, _absolu(dest)], DELAI_GIT, env=_env_git(acces))


def git_recuperer_ordres(acces, rep, branche):
    return _lancer(["git", "-C", _absolu(rep), "fetch", "--quiet", "origin", _branche(branche)], DELAI_GIT,
                   env=_env_git(acces))


def git_recuperer_miroir(acces, rep):
    return _lancer(["git", "-C", _absolu(rep), "fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*"],
                   DELAI_GIT, env=_env_git(acces))


def git_rebaser(acces, rep, branche, nom, courriel):
    return _lancer(["git", "-C", _absolu(rep), "-c", "user.name=" + nom, "-c", "user.email=" + courriel,
                    "pull", "--quiet", "--rebase", "origin", _branche(branche)], DELAI_GIT, env=_env_git(acces))


def git_rebaser_abandonner(rep):
    return _lancer(["git", "-C", _absolu(rep), "rebase", "--abort"], DELAI_GIT, tolerer=True)


def git_modifications(rep):
    """Sortie de ``git status --porcelain`` (vide : rien à valider)."""
    return _lancer(["git", "-C", _absolu(rep), "status", "--porcelain"], DELAI_GIT).sortie


def git_ajouter(rep, chemin_relatif):
    return _lancer(["git", "-C", _absolu(rep), "add", "--", chemin_relatif], DELAI_GIT)


def git_index_vide(rep):
    return _lancer(["git", "-C", _absolu(rep), "diff", "--cached", "--quiet"], DELAI_GIT, tolerer=True).code == 0


def git_valider(rep, message, nom, courriel):
    return _lancer(["git", "-C", _absolu(rep), "-c", "user.name=" + nom, "-c", "user.email=" + courriel,
                    "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", message], DELAI_GIT)


def git_pousser(acces, rep, branche):
    return _lancer(["git", "-C", _absolu(rep), "push", "--quiet", "origin", "HEAD:refs/heads/" + _branche(branche)],
                   DELAI_GIT, env=_env_git(acces))


def git_en_avance(rep, branche):
    r = _lancer(["git", "-C", _absolu(rep), "rev-list", "--count", "origin/%s..HEAD" % _branche(branche)],
                DELAI_GIT, tolerer=True)
    try:
        return int(r.sortie.strip()) if r.code == 0 else 0
    except ValueError:
        return 0


def git_commit_existe(rep, sha):
    return _lancer(["git", "-C", _absolu(rep), "cat-file", "-e", _sha(sha) + "^{commit}"], DELAI_GIT,
                   tolerer=True).code == 0


def git_archive(rep, sha, fichier_sortie):
    """Archive tar du commit (modes normalisés par ``tar.umask``), écrite dans ``fichier_sortie``."""
    _lancer(["git", "-C", _absolu(rep), "-c", "tar.umask=0022", "archive", "--format=tar", _sha(sha)], DELAI_GIT,
            sortie_fichier=_absolu(fichier_sortie))
