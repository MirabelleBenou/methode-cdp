"""Les opérations de fichiers, enfermées dans des zones.

Rien ne s'efface (tout part à la corbeille de la zone), rien ne s'exécute (aucun bit d'exécution posé), jamais
d'écrasement silencieux, jamais de chemin hors de la zone. La seule suppression réelle est ``vider-la-corbeille``,
qui exige un ``go`` dans l'ordre.
"""

import errno
import os
import posixpath
import shutil
import stat
import tarfile
import zipfile

from . import ecriture, reseau, zones
from .compterendu import REFUSE, REUSSI, taille
from .filtre import filtrer

GO = 1 << 30
MAX_ENTREES_LISTE = 500


class ErreurOperation(Exception):
    pass


# ----------------------------------------------------------------------------------------------
# Aides communes
# ----------------------------------------------------------------------------------------------

def _zone(ctx, nom):
    return ctx.cfg.zones[nom]


def _proprietaire_zone(zone):
    return ecriture.proprietaire(zones.racine(zone))


def _libre(zone):
    return shutil.disk_usage(zones.racine(zone)).free


def _verifier_place(zone, besoin=0):
    """Refuse si l'opération laisserait moins que ``place_min_go`` de la zone."""
    libre = _libre(zone)
    if libre - besoin < zone.place_min_go * GO:
        raise ErreurOperation("place insuffisante dans la zone %s : %s libres, %s requis plus un minimum de %s Go"
                              % (zone.nom, taille(libre), taille(besoin), zone.place_min_go))


def _chemin(zone, rel, **kw):
    try:
        return zones.resoudre(zone, rel, **kw)
    except zones.ErreurChemin as e:
        raise ErreurOperation(str(e))


def _libre_nom(chemin):
    if not os.path.lexists(chemin):
        return chemin
    n = 2
    while os.path.lexists("%s.%d" % (chemin, n)):
        n += 1
    return "%s.%d" % (chemin, n)


def _sous_dossier_propre(zone, dossier):
    """Crée ``dossier`` (parents compris) en vérifiant qu'il reste dans la zone."""
    base = zones.racine(zone)
    uid, gid = ecriture.proprietaire(base)
    ecriture.creer_dossiers(dossier, uid, gid)
    reel = os.path.realpath(dossier)
    if reel != base and not reel.startswith(base + os.sep):
        raise ErreurOperation("le dossier sort de la zone %s" % zone.nom)


def envoyer_a_la_corbeille(zone, chemin_abs, ordre_id):
    """Déplace ``chemin_abs`` vers ``<zone>/_corbeille/<id de l'ordre>/<chemin relatif>`` ; retourne la destination."""
    base = zones.racine(zone)
    rel = os.path.relpath(chemin_abs, base)
    if rel == "." or rel.startswith(".."):
        raise ErreurOperation("la racine de la zone ne part pas à la corbeille")
    dest = os.path.join(base, zones.NOM_CORBEILLE, ordre_id, rel)
    _sous_dossier_propre(zone, os.path.dirname(dest))
    dest = _libre_nom(dest)
    try:
        os.rename(chemin_abs, dest)
    except OSError as e:
        if e.errno == errno.EXDEV:
            raise ErreurOperation("%s traverse un point de montage : mise à la corbeille impossible" % rel)
        raise
    return dest


def _doit_exister(chemin, rel):
    if not os.path.lexists(chemin):
        raise ErreurOperation("introuvable : %s" % rel)


# ----------------------------------------------------------------------------------------------
# lister, empreinte, creer-dossier
# ----------------------------------------------------------------------------------------------

def op_lister(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    cible = _chemin(zone, op["chemin"], vide_ok=True)
    _doit_exister(cible, op["chemin"])
    if not os.path.isdir(cible):
        raise ErreurOperation("pas un dossier : %s" % op["chemin"])
    profondeur = op.get("profondeur", 1)
    entrees = []
    tronque = [False]

    def parcourir(dossier, niveau):
        try:
            with os.scandir(dossier) as it:
                noms = sorted(it, key=lambda e: e.name)
        except OSError as e:
            raise ErreurOperation("lecture impossible : %s" % e)
        for e in noms:
            if len(entrees) >= MAX_ENTREES_LISTE:
                tronque[0] = True
                return
            rel = os.path.relpath(e.path, zones.racine(zone))
            if e.is_symlink():
                entrees.append(("lien", 0, rel))
            elif e.is_dir(follow_symlinks=False):
                entrees.append(("dossier", 0, rel))
                if niveau < profondeur:
                    parcourir(e.path, niveau + 1)
            elif e.is_file(follow_symlinks=False):
                entrees.append(("fichier", e.stat(follow_symlinks=False).st_size, rel))
            else:
                entrees.append(("autre", 0, rel))
            ctx.tick()

    parcourir(cible, 1)
    lignes = ["%s %s %s" % (t, taille(n) if t == "fichier" else "-", r) for t, n, r in entrees]
    lignes.append("%d entrée(s)%s ; place libre de la zone : %s" % (
        len(entrees), " (liste tronquée à %d)" % MAX_ENTREES_LISTE if tronque[0] else "", taille(_libre(zone))))
    return lignes


def op_empreinte(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    lignes = []
    for rel in op["chemins"]:
        cible = _chemin(zone, rel)
        _doit_exister(cible, rel)
        if not os.path.isfile(cible):
            raise ErreurOperation("pas un fichier : %s" % rel)
        lignes.append("%s  %s  %s" % (ecriture.sha256_fichier(cible, ctx.tick), taille(os.path.getsize(cible)), rel))
    return lignes


def op_creer_dossier(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    cible = _chemin(zone, op["chemin"], corbeille_ok=False)
    if os.path.isdir(cible) and not os.path.islink(cible):
        return ["déjà présent : %s" % op["chemin"]]
    if os.path.lexists(cible):
        raise ErreurOperation("existe déjà et n'est pas un dossier : %s" % op["chemin"])
    _verifier_place(zone)
    _sous_dossier_propre(zone, cible)
    return ["créé : %s" % op["chemin"]]


# ----------------------------------------------------------------------------------------------
# telecharger
# ----------------------------------------------------------------------------------------------

def op_telecharger(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    cible = _chemin(zone, op["chemin"], corbeille_ok=False)
    if os.path.lexists(cible):
        raise ErreurOperation("la cible existe déjà : %s (jamais d'écrasement)" % op["chemin"])
    try:
        src = reseau.analyser_source(op["source"], ctx.cfg)
    except reseau.ErreurSource as e:
        raise ErreurOperation(str(e))
    _verifier_place(zone)
    _sous_dossier_propre(zone, os.path.dirname(cible))
    part = cible + ".part"
    if os.path.lexists(part):
        envoyer_a_la_corbeille(zone, part, ordre.id)
    uid, gid = _proprietaire_zone(zone)
    try:
        octets, somme = reseau.telecharger(src.url, src.hotes_ok, part, sha256=op.get("sha256"),
                                           place_min_octets=int(zone.place_min_go * GO), battement=ctx.tick)
        os.chmod(part, ecriture.MODE_FICHIER)
        ecriture.appliquer_proprietaire(part, uid, gid)
        os.rename(part, cible)
    except reseau.ErreurReseau as e:
        if os.path.lexists(part):
            os.remove(part)
        raise ErreurOperation("téléchargement refusé : %s" % filtrer(str(e)))
    except BaseException:
        if os.path.lexists(part):
            os.remove(part)
        raise
    return ["téléchargé : %s (%s, sha256 %s)" % (op["chemin"], taille(octets), somme)]


# ----------------------------------------------------------------------------------------------
# copier, deplacer
# ----------------------------------------------------------------------------------------------

def _inventaire(chemin):
    """Taille totale d'un fichier ou d'un arbre ; refuse liens et fichiers spéciaux."""
    st = os.lstat(chemin)
    if stat.S_ISREG(st.st_mode):
        return st.st_size
    if not stat.S_ISDIR(st.st_mode):
        raise ErreurOperation("lien symbolique ou fichier spécial refusé : %s" % chemin)
    total = 0
    for racine, dirs, fichiers in os.walk(chemin):
        for nom in dirs + fichiers:
            chemin_e = os.path.join(racine, nom)
            s = os.lstat(chemin_e)
            if stat.S_ISREG(s.st_mode):
                total += s.st_size
            elif not stat.S_ISDIR(s.st_mode):
                raise ErreurOperation("lien symbolique ou fichier spécial refusé : %s" % chemin_e)
    return total


def _copier_fichier(src, dst, uid, gid, tick):
    with open(src, "rb") as a, open(dst, "wb") as b:
        while True:
            bloc = a.read(1 << 20)
            if not bloc:
                break
            b.write(bloc)
            tick()
        b.flush()
        os.fsync(b.fileno())
    os.chmod(dst, ecriture.MODE_FICHIER)
    ecriture.appliquer_proprietaire(dst, uid, gid)


def _copier_arbre(src, dst, uid, gid, tick):
    if os.path.isfile(src):
        _copier_fichier(src, dst, uid, gid, tick)
        return
    os.mkdir(dst, ecriture.MODE_DOSSIER)
    os.chmod(dst, ecriture.MODE_DOSSIER)
    ecriture.appliquer_proprietaire(dst, uid, gid)
    for nom in sorted(os.listdir(src)):
        _copier_arbre(os.path.join(src, nom), os.path.join(dst, nom), uid, gid, tick)


def _copie_vers(zone_vers, src, vers, ordre_id, tick):
    """Copie ``src`` vers ``vers`` par un nom temporaire voisin puis renommage."""
    uid, gid = _proprietaire_zone(zone_vers)
    tmp = _libre_nom(os.path.join(os.path.dirname(vers), ".copie-%s" % ordre_id))
    try:
        _copier_arbre(src, tmp, uid, gid, tick)
        os.rename(tmp, vers)
    except BaseException:
        if os.path.isdir(tmp) and not os.path.islink(tmp):
            shutil.rmtree(tmp, ignore_errors=True)
        elif os.path.lexists(tmp):
            os.remove(tmp)
        raise


def _preparer_copie_ou_deplacement(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    zone_vers = _zone(ctx, op.get("zone_vers", op["zone"]))
    de = _chemin(zone, op["de"])
    if posixpath.normpath(op["de"]) == zones.NOM_CORBEILLE:
        raise ErreurOperation("la corbeille elle-même ne se copie ni ne se déplace")
    vers = _chemin(zone_vers, op["vers"], corbeille_ok=False)
    _doit_exister(de, op["de"])
    if os.path.realpath(de) == os.path.realpath(vers) or de == vers:
        raise ErreurOperation("la source et la destination sont identiques")
    if os.path.isdir(de) and not os.path.islink(de):
        rd, rv = os.path.realpath(de), os.path.realpath(vers)
        if rv.startswith(rd + os.sep):
            raise ErreurOperation("la destination est dans la source")
    return zone, zone_vers, de, vers


def _gerer_existant(op, zone_vers, vers, ordre_id, lignes):
    if os.path.lexists(vers):
        if op.get("si_existe", "refuser") != "remplacer":
            raise ErreurOperation("la cible existe déjà : %s (si_existe : remplacer pour la mettre à la corbeille)"
                                  % op["vers"])
        mise = envoyer_a_la_corbeille(zone_vers, vers, ordre_id)
        lignes.append("ancienne cible mise à la corbeille : %s" % os.path.relpath(mise, zones.racine(zone_vers)))


def op_copier(ctx, op, ordre):
    zone, zone_vers, de, vers = _preparer_copie_ou_deplacement(ctx, op, ordre)
    besoin = _inventaire(de)
    _verifier_place(zone_vers, besoin)
    lignes = []
    _gerer_existant(op, zone_vers, vers, ordre.id, lignes)
    _sous_dossier_propre(zone_vers, os.path.dirname(vers))
    _copie_vers(zone_vers, de, vers, ordre.id, ctx.tick)
    lignes.append("copié : %s → %s (%s)" % (op["de"], op["vers"], taille(besoin)))
    return lignes


def op_deplacer(ctx, op, ordre):
    zone, zone_vers, de, vers = _preparer_copie_ou_deplacement(ctx, op, ordre)
    lignes = []
    _gerer_existant(op, zone_vers, vers, ordre.id, lignes)
    _sous_dossier_propre(zone_vers, os.path.dirname(vers))
    try:
        os.rename(de, vers)
        lignes.append("déplacé : %s → %s" % (op["de"], op["vers"]))
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
        besoin = _inventaire(de)
        _verifier_place(zone_vers, besoin)
        _copie_vers(zone_vers, de, vers, ordre.id, ctx.tick)
        mise = envoyer_a_la_corbeille(zone, de, ordre.id)
        lignes.append("déplacé entre systèmes de fichiers : copié vers %s, source mise à la corbeille (%s)"
                      % (op["vers"], os.path.relpath(mise, zones.racine(zone))))
    return lignes


# ----------------------------------------------------------------------------------------------
# decompresser
# ----------------------------------------------------------------------------------------------

def _nom_membre(nom):
    if "\0" in nom:
        raise ErreurOperation("caractère nul dans un nom de membre")
    n = nom[2:] if nom.startswith("./") else nom
    n = n.rstrip("/")
    if n.startswith("/"):
        raise ErreurOperation("chemin absolu dans l'archive : %r" % nom)
    if ".." in n.split("/"):
        raise ErreurOperation("composant '..' dans l'archive : %r" % nom)
    return posixpath.normpath(n) if n else ""


def _membres_tar(chemin, mode):
    tf = tarfile.open(chemin, mode)
    try:
        membres = []
        for m in tf.getmembers():
            n = _nom_membre(m.name)
            if m.issym() or m.islnk():
                raise ErreurOperation("lien dans l'archive refusé : %r" % m.name)
            if not (m.isreg() or m.isdir()):
                raise ErreurOperation("fichier spécial dans l'archive refusé : %r" % m.name)
            if n:
                membres.append((n, m.isdir(), m.size, m))
    except BaseException:
        tf.close()
        raise
    return tf, membres


def _membres_zip(chemin):
    zf = zipfile.ZipFile(chemin)
    try:
        membres = []
        for i in zf.infolist():
            n = _nom_membre(i.filename)
            if i.flag_bits & 0x1:
                raise ErreurOperation("membre chiffré refusé : %r" % i.filename)
            type_unix = (i.external_attr >> 16) & 0o170000
            if type_unix not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ErreurOperation("lien ou fichier spécial dans l'archive refusé : %r" % i.filename)
            if n:
                membres.append((n, i.is_dir(), i.file_size, i))
    except BaseException:
        zf.close()
        raise
    return zf, membres


def _ecrire_membre(flux, dest, annonce, uid, gid, tick):
    ecrit = 0
    with open(dest, "wb") as f:
        while True:
            bloc = flux.read(1 << 20)
            if not bloc:
                break
            ecrit += len(bloc)
            if ecrit > annonce:
                raise ErreurOperation("un membre dépasse la taille annoncée : %s" % os.path.basename(dest))
            f.write(bloc)
            tick()
        f.flush()
        os.fsync(f.fileno())
    os.chmod(dest, ecriture.MODE_FICHIER)
    ecriture.appliquer_proprietaire(dest, uid, gid)


def op_decompresser(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    archive = _chemin(zone, op["archive"])
    vers = _chemin(zone, op["vers"], corbeille_ok=False)
    _doit_exister(archive, op["archive"])
    if not os.path.isfile(archive):
        raise ErreurOperation("pas un fichier : %s" % op["archive"])
    if os.path.lexists(vers):
        raise ErreurOperation("la destination existe déjà : %s" % op["vers"])
    minuscule = op["archive"].lower()
    lecteur = None
    try:
        try:
            if minuscule.endswith(".zip"):
                lecteur, membres = _membres_zip(archive)
            elif minuscule.endswith((".tar.gz", ".tgz")):
                lecteur, membres = _membres_tar(archive, "r:gz")
            else:
                lecteur, membres = _membres_tar(archive, "r:")
        except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError) as e:
            raise ErreurOperation("archive illisible : %s" % e)
        total = sum(t for _, est_dossier, t, _ in membres if not est_dossier)
        _verifier_place(zone, int(total * 1.1) + 1)
        parent = os.path.dirname(vers)
        _sous_dossier_propre(zone, parent)
        uid, gid = _proprietaire_zone(zone)
        tmp = _libre_nom(os.path.join(parent, ".decomp-%s" % ordre.id))
        os.mkdir(tmp, ecriture.MODE_DOSSIER)
        os.chmod(tmp, ecriture.MODE_DOSSIER)
        ecriture.appliquer_proprietaire(tmp, uid, gid)
        try:
            for nom, est_dossier, annonce, m in membres:
                dest = os.path.join(tmp, nom)
                if os.path.commonpath([tmp, os.path.normpath(dest)]) != tmp:
                    raise ErreurOperation("membre hors du dossier d'extraction : %r" % nom)
                if est_dossier:
                    ecriture.creer_dossiers(dest, uid, gid)
                    continue
                ecriture.creer_dossiers(os.path.dirname(dest), uid, gid)
                if os.path.lexists(dest) and os.path.isdir(dest):
                    raise ErreurOperation("conflit de nom dans l'archive : %r" % nom)
                if isinstance(lecteur, zipfile.ZipFile):
                    with lecteur.open(m) as flux:
                        _ecrire_membre(flux, dest, annonce, uid, gid, ctx.tick)
                else:
                    _ecrire_membre(lecteur.extractfile(m), dest, annonce, uid, gid, ctx.tick)
            os.rename(tmp, vers)
        except BaseException:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
    finally:
        if lecteur is not None:
            lecteur.close()
    n_fichiers = sum(1 for _, d, _, _ in membres if not d)
    return ["décompressé : %s → %s (%d fichiers, %s)" % (op["archive"], op["vers"], n_fichiers, taille(total))]


# ----------------------------------------------------------------------------------------------
# basculer, corbeille
# ----------------------------------------------------------------------------------------------

def op_basculer(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    prepare = _chemin(zone, op["prepare"], corbeille_ok=False)
    servi = _chemin(zone, op["servi"], corbeille_ok=False)
    _doit_exister(prepare, op["prepare"])
    lignes = []
    if os.path.lexists(servi):
        mise = envoyer_a_la_corbeille(zone, servi, ordre.id)
        lignes.append("ancien servi mis à la corbeille : %s" % os.path.relpath(mise, zones.racine(zone)))
    else:
        lignes.append("aucun servi en place : %s" % op["servi"])
    _sous_dossier_propre(zone, os.path.dirname(servi))
    os.rename(prepare, servi)
    lignes.append("%s est maintenant servi sous %s" % (op["prepare"], op["servi"]))
    return lignes


def op_mettre_a_la_corbeille(ctx, op, ordre):
    zone = _zone(ctx, op["zone"])
    cible = _chemin(zone, op["chemin"], corbeille_ok=False)
    _doit_exister(cible, op["chemin"])
    mise = envoyer_a_la_corbeille(zone, cible, ordre.id)
    return ["mis à la corbeille : %s → %s" % (op["chemin"], os.path.relpath(mise, zones.racine(zone)))]


def _poids(chemin):
    total = 0
    if os.path.islink(chemin) or os.path.isfile(chemin):
        return os.lstat(chemin).st_size
    for racine, _, fichiers in os.walk(chemin):
        for f in fichiers:
            try:
                total += os.lstat(os.path.join(racine, f)).st_size
            except OSError:
                pass
    return total


def op_vider_la_corbeille(ctx, op, ordre):
    if not str(ordre.champs.get("go", "")).strip():
        raise ErreurOperation("vider la corbeille exige un 'go' dans l'ordre")
    zone = _zone(ctx, op["zone"])
    base = zones.racine(zone)
    corbeille = os.path.join(base, zones.NOM_CORBEILLE)
    if not os.path.lexists(corbeille):
        return ["la corbeille de la zone %s n'existe pas : rien à vider" % zone.nom]
    if os.path.islink(corbeille) or not os.path.isdir(corbeille) or os.path.realpath(corbeille) != corbeille:
        raise ErreurOperation("la corbeille de la zone %s n'est pas un dossier ordinaire" % zone.nom)
    if "id_corbeille" in op:
        cibles = [os.path.join(corbeille, op["id_corbeille"])]
        if not os.path.lexists(cibles[0]):
            raise ErreurOperation("rien dans la corbeille sous l'identifiant %s" % op["id_corbeille"])
    else:
        cibles = [os.path.join(corbeille, n) for n in sorted(os.listdir(corbeille))]
    libere = 0
    for c in cibles:
        libere += _poids(c)
        if os.path.isdir(c) and not os.path.islink(c):
            shutil.rmtree(c)
        else:
            os.remove(c)
        ctx.tick()
    return ["corbeille de la zone %s vidée : %d élément(s), %s libérés" % (zone.nom, len(cibles), taille(libere))]


OPERATIONS = {
    "lister": op_lister,
    "empreinte": op_empreinte,
    "creer-dossier": op_creer_dossier,
    "telecharger": op_telecharger,
    "copier": op_copier,
    "deplacer": op_deplacer,
    "decompresser": op_decompresser,
    "basculer": op_basculer,
    "mettre-a-la-corbeille": op_mettre_a_la_corbeille,
    "vider-la-corbeille": op_vider_la_corbeille,
}


def jouer(ctx, compte, ordre):
    """Joue les opérations dans l'ordre ; la première en erreur arrête l'ordre."""
    ops = ordre.champs["operations"]
    lignes = compte.section("Opérations")
    for i, op in enumerate(ops, 1):
        intitule = "%d. %s" % (i, op["operation"])
        ctx.log("ordre %s : opération %s" % (ordre.id, intitule))
        try:
            detail = OPERATIONS[op["operation"]](ctx, op, ordre)
        except (ErreurOperation, zones.ErreurChemin) as e:
            lignes.append("- %s : **ÉCHEC** : %s" % (intitule, e))
            _bilan(compte, i - 1, len(ops), intitule, str(e))
            return REFUSE
        except OSError as e:
            lignes.append("- %s : **ÉCHEC** (erreur système) : %s" % (intitule, e))
            _bilan(compte, i - 1, len(ops), intitule, "erreur système : %s" % e)
            return REFUSE
        lignes.append("- %s : ok" % intitule)
        lignes.extend("  - %s" % d for d in detail)
    compte.ligne("Résumé", "- %d opération(s) réussie(s) sur %d" % (len(ops), len(ops)))
    return REUSSI


def _bilan(compte, faites, total, intitule, raison):
    compte.ligne("Résumé", "- arrêt à l'opération %s : %s" % (intitule, raison))
    compte.ligne("Résumé", "- %d opération(s) faite(s) avant l'arrêt sur %d" % (faites, total))
    compte.decider("corriger l'opération en échec et envoyer un nouvel ordre (celui-ci n'est jamais rejoué)")
