"""Écritures de fichiers : toujours par un fichier temporaire du même dossier puis ``os.replace``.

Propriétaire et groupe sont ceux du dossier d'accueil ; droits 644 (fichiers) et 755 (dossiers) ; aucun bit
d'exécution posé, sauf demande explicite (fichiers de l'archive de l'application qui le portent).
"""

import errno
import hashlib
import json
import os
import tempfile

MODE_FICHIER = 0o644
MODE_EXEC = 0o755
MODE_DOSSIER = 0o755


def proprietaire(chemin):
    st = os.stat(chemin)
    return st.st_uid, st.st_gid


def appliquer_proprietaire(chemin, uid, gid):
    try:
        st = os.lstat(chemin)
        if st.st_uid != uid or st.st_gid != gid:
            os.chown(chemin, uid, gid, follow_symlinks=False)
    except PermissionError:
        pass


def creer_dossiers(dossier, uid, gid):
    """Crée ``dossier`` et ses parents manquants (755, propriétaire imposé). Retourne la liste des créés."""
    crees = []
    manquants = []
    courant = os.path.abspath(dossier)
    while not os.path.isdir(courant):
        manquants.append(courant)
        parent = os.path.dirname(courant)
        if parent == courant:
            break
        courant = parent
    for d in reversed(manquants):
        try:
            os.mkdir(d, MODE_DOSSIER)
        except FileExistsError:
            if not os.path.isdir(d):
                raise
            continue
        os.chmod(d, MODE_DOSSIER)
        appliquer_proprietaire(d, uid, gid)
        crees.append(d)
    return crees


def _temporaire(dest):
    d = os.path.dirname(os.path.abspath(dest))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".dep-", suffix=".tmp")
    return fd, tmp


def ecrire_octets(dest, octets, mode=MODE_FICHIER, uid=None, gid=None):
    fd, tmp = _temporaire(dest)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(octets)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        if uid is not None:
            appliquer_proprietaire(tmp, uid, gid)
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def ecrire_texte(dest, texte, mode=MODE_FICHIER, uid=None, gid=None):
    ecrire_octets(dest, texte.encode("utf-8"), mode, uid, gid)


def ecrire_json(dest, objet, mode=0o600):
    ecrire_octets(dest, (json.dumps(objet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"), mode)


def lire_json(chemin, defaut=None):
    try:
        with open(chemin, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except FileNotFoundError:
        return defaut


def sha256_fichier(chemin, battement=None):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        while True:
            bloc = f.read(1 << 20)
            if not bloc:
                break
            h.update(bloc)
            if battement:
                battement()
    return h.hexdigest()


def retirer_dossiers_vides(depart, borne):
    """Retire ``depart`` puis ses parents tant qu'ils sont vides, sans jamais atteindre ``borne``."""
    borne = os.path.abspath(borne)
    courant = os.path.abspath(depart)
    retires = []
    while courant != borne and courant.startswith(borne + os.sep):
        try:
            os.rmdir(courant)
        except OSError as e:
            if e.errno in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT, errno.EACCES, errno.EBUSY):
                break
            raise
        retires.append(courant)
        courant = os.path.dirname(courant)
    return retires
