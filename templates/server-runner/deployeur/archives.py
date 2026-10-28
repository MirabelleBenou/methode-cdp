"""L'archive d'un commit de l'application (tar produit par ``git archive``) et sa pose dans le dossier déployé.

Identité d'un fichier : son sha256 et son bit d'exécution pour le propriétaire. Aucun autre bit n'est comparé.
À la pose : 755 si le fichier est exécutable dans l'archive, 644 sinon.
"""

import fnmatch
import hashlib
import os
import posixpath
import stat
import tarfile

from . import ecriture


class ArchiveInvalide(Exception):
    pass


def est_protege(chemin, motifs):
    """``chemin`` (relatif, séparateurs '/') correspond-il à un chemin protégé ?

    Un motif terminé par '/' protège un dossier de la racine et tout ce qu'il contient ; un motif sans '/'
    s'applique au nom de chaque fichier à n'importe quelle profondeur (``fnmatch``) ; un autre motif s'applique
    au chemin complet.
    """
    for m in motifs:
        if m.endswith("/"):
            d = m.rstrip("/")
            if chemin == d or chemin.startswith(d + "/"):
                return True
        elif "/" not in m:
            if any(fnmatch.fnmatchcase(part, m) for part in chemin.split("/")):
                return True
        elif fnmatch.fnmatchcase(chemin, m):
            return True
    return False


class Archive:
    """Lecture d'une archive tar. Seuls les fichiers réguliers et les dossiers sont admis."""

    def __init__(self, chemin):
        self.chemin = chemin
        self.fichiers = {}   # chemin -> {"sha256", "exec", "taille"}
        self._tar = None
        try:
            self._tar = tarfile.open(chemin, "r:")
            self._lire()
        except (tarfile.TarError, OSError) as e:
            self.fermer()
            raise ArchiveInvalide("archive illisible : %s" % e)
        except ArchiveInvalide:
            self.fermer()
            raise

    def _lire(self):
        for m in self._tar:
            nom = m.name
            if nom.startswith("./"):
                nom = nom[2:]
            nom = nom.rstrip("/")
            if not nom:
                continue
            if nom.startswith("/") or ".." in nom.split("/") or "\0" in nom:
                raise ArchiveInvalide("chemin d'archive refusé : %r" % m.name)
            if m.isdir():
                continue
            if not m.isreg():
                raise ArchiveInvalide("membre d'archive non régulier (lien ou fichier spécial) : %r" % m.name)
            nom = posixpath.normpath(nom)
            h = hashlib.sha256()
            f = self._tar.extractfile(m)
            while True:
                bloc = f.read(1 << 20)
                if not bloc:
                    break
                h.update(bloc)
            self.fichiers[nom] = {"sha256": h.hexdigest(), "exec": bool(m.mode & 0o100), "taille": m.size,
                                  "_membre": m}

    def lire(self, chemin):
        return self._tar.extractfile(self.fichiers[chemin]["_membre"])

    def manifeste(self):
        return {c: {"sha256": v["sha256"], "exec": v["exec"]} for c, v in sorted(self.fichiers.items())}

    def fermer(self):
        if self._tar is not None:
            self._tar.close()
            self._tar = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.fermer()
        return False


def identite_fichier(chemin):
    """(sha256, exécutable) d'un fichier régulier du disque ; None si absent ou pas régulier."""
    try:
        st = os.lstat(chemin)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    return ecriture.sha256_fichier(chemin), bool(st.st_mode & 0o100)


def comparer(archive, dossier):
    """Liste des écarts entre l'archive et le dossier : (chemin, raison)."""
    ecarts = []
    for chemin, v in sorted(archive.fichiers.items()):
        ident = identite_fichier(os.path.join(dossier, chemin))
        if ident is None:
            ecarts.append((chemin, "absent ou non régulier"))
        elif ident[0] != v["sha256"]:
            ecarts.append((chemin, "contenu différent"))
        elif ident[1] != v["exec"]:
            ecarts.append((chemin, "bit d'exécution différent"))
    return ecarts


def fichiers_hors_archive(dossier, connus, proteges, limite=200):
    """Fichiers présents dans ``dossier`` mais absents de ``connus`` (ensemble de chemins) ; protégés exclus."""
    trouves = []
    total = 0
    for racine, dirs, fichiers in os.walk(dossier):
        rel_racine = os.path.relpath(racine, dossier)
        rel_racine = "" if rel_racine == "." else rel_racine.replace(os.sep, "/")
        dirs[:] = sorted(d for d in dirs if not est_protege((rel_racine + "/" + d).lstrip("/") + "/x", proteges)
                         and not os.path.islink(os.path.join(racine, d)))
        for nom in sorted(fichiers):
            rel = (rel_racine + "/" + nom).lstrip("/")
            if est_protege(rel, proteges) or rel in connus:
                continue
            total += 1
            if len(trouves) < limite:
                trouves.append(rel)
    return trouves, total


def poser(archive, dossier, retirer_si_absent, proteges, uid, gid, battement=None):
    """Pose l'archive dans ``dossier`` ; retire les fichiers de ``retirer_si_absent`` (manifeste) absents de
    l'archive. Jamais un chemin protégé, jamais un fichier inconnu des deux. Retourne un dict de comptes."""
    base = os.path.realpath(dossier)
    poses, inchanges, ecrases, retires = [], [], [], []
    for chemin, v in sorted(archive.fichiers.items()):
        if est_protege(chemin, proteges):
            raise ArchiveInvalide("chemin protégé dans l'archive : %s" % chemin)
        dest = os.path.join(dossier, chemin)
        parent = os.path.dirname(dest)
        ecriture.creer_dossiers(parent, uid, gid)
        reel_parent = os.path.realpath(parent)
        if reel_parent != base and not reel_parent.startswith(base + os.sep):
            raise ArchiveInvalide("le chemin sort du dossier déployé : %s" % chemin)
        if os.path.islink(dest) or os.path.isdir(dest):
            raise ArchiveInvalide("un lien ou un dossier occupe la place du fichier %s" % chemin)
        ident = identite_fichier(dest)
        if ident is not None and ident[0] == v["sha256"] and ident[1] == v["exec"]:
            inchanges.append(chemin)
            continue
        if ident is not None and chemin not in retirer_si_absent:
            ecrases.append(chemin)
        flux = archive.lire(chemin)
        fd_octets = flux.read()
        ecriture.ecrire_octets(dest, fd_octets, ecriture.MODE_EXEC if v["exec"] else ecriture.MODE_FICHIER, uid, gid)
        poses.append(chemin)
        if battement:
            battement()
    for chemin in sorted(retirer_si_absent):
        if chemin in archive.fichiers or est_protege(chemin, proteges):
            continue
        dest = os.path.join(dossier, chemin)
        if os.path.islink(dest) or not os.path.isfile(dest):
            continue
        os.remove(dest)
        retires.append(chemin)
        ecriture.retirer_dossiers_vides(os.path.dirname(dest), dossier)
    return {"poses": poses, "inchanges": inchanges, "ecrases_inconnus": ecrases, "retires": retires}
