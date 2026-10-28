"""La base et les volumes irremplaçables : contrôles du projet, lecture des comptes, sauvegarde, purge.

Le programme ne contient aucun chemin qui écrive dans la base : seules des lectures (transaction en lecture seule)
et la sauvegarde (``dump``) passent par le conteneur de la base. Aucune restauration.
"""

import json
import os
import re
import tarfile

from . import commandes, compterendu, ecriture
from .filtre import filtrer

LABEL_PROJET = "com.docker.compose.project"
LABEL_DOSSIER = "com.docker.compose.project.working_dir"
LABEL_SERVICE = "com.docker.compose.service"


class ErreurBase(Exception):
    pass


# ----------------------------------------------------------------------------------------------
# Invariant 2 : le bon projet ou rien
# ----------------------------------------------------------------------------------------------

def _analyser_ps(texte):
    """``compose ps --format json`` : un tableau JSON ou un objet par ligne selon la version."""
    texte = (texte or "").strip()
    if not texte:
        return []
    try:
        obj = json.loads(texte)
        return obj if isinstance(obj, list) else [obj]
    except ValueError:
        pass
    out = []
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if ligne:
            out.append(json.loads(ligne))
    return out


def conteneurs_projet(app):
    """Liste des conteneurs du projet (service, nom, état, santé) ; lève ErreurBase si illisible."""
    try:
        brut = commandes.compose_ps(app.projet, app.dossier, app.fichier_compose)
        res = []
        for c in _analyser_ps(brut):
            res.append({"service": c.get("Service", ""), "nom": c.get("Name", ""), "etat": c.get("State", ""),
                        "sante": c.get("Health", ""), "statut": c.get("Status", "")})
        return res
    except (commandes.ErreurCommande, ValueError, AttributeError) as e:
        raise ErreurBase("état du projet illisible : %s" % filtrer(str(e)))


class Controle:
    def __init__(self):
        self.problemes = []
        self.conteneurs = []
        self.image_db = None
        self.volumes = []

    @property
    def ok(self):
        return not self.problemes


def controler_projet(app):
    """Vérifie, sans rien toucher : projet, conteneur de la base (étiquettes), trois volumes, montage de la base."""
    c = Controle()
    try:
        c.conteneurs = conteneurs_projet(app)
    except ErreurBase as e:
        c.problemes.append(str(e))
        return c
    db = [x for x in c.conteneurs if x["service"] == app.service_db]
    if not db:
        c.problemes.append("le projet %s n'a aucun conteneur du service %s en marche" % (app.projet, app.service_db))
        return c
    if db[0]["etat"] != "running":
        c.problemes.append("le service %s n'est pas en marche (%s)" % (app.service_db, db[0]["etat"]))
    try:
        info = json.loads(commandes.docker_inspect(app.conteneur_db))
        info = info[0]
        etiquettes = (info.get("Config") or {}).get("Labels") or {}
        c.image_db = (info.get("Config") or {}).get("Image")
        if etiquettes.get(LABEL_PROJET) != app.projet:
            c.problemes.append("le conteneur %s n'est pas du projet %s (étiquette : %r)"
                               % (app.conteneur_db, app.projet, etiquettes.get(LABEL_PROJET)))
        if os.path.normpath(etiquettes.get(LABEL_DOSSIER) or "/?") != os.path.normpath(app.dossier):
            c.problemes.append("le conteneur %s n'est pas rattaché au dossier %s (étiquette : %r)"
                               % (app.conteneur_db, app.dossier, etiquettes.get(LABEL_DOSSIER)))
        if etiquettes.get(LABEL_SERVICE) not in (None, app.service_db):
            c.problemes.append("le conteneur %s n'est pas le service %s" % (app.conteneur_db, app.service_db))
        montages = [m for m in (info.get("Mounts") or []) if m.get("Destination") == app.montage_base]
        if not montages or montages[0].get("Name") != app.volume_base or montages[0].get("Type") != "volume":
            c.problemes.append("le conteneur %s ne monte pas le volume %s sur %s"
                               % (app.conteneur_db, app.volume_base, app.montage_base))
        if not c.image_db:
            c.problemes.append("image du conteneur %s introuvable" % app.conteneur_db)
    except (commandes.ErreurCommande, ValueError, IndexError, KeyError, AttributeError, TypeError) as e:
        c.problemes.append("conteneur %s illisible : %s" % (app.conteneur_db, filtrer(str(e))))
    for volume in (app.volume_base, app.volume_ecussons, app.volume_depots_bruts):
        try:
            v = json.loads(commandes.docker_volume_inspect(volume))[0]
            etiq = v.get("Labels") or {}
            if etiq.get(LABEL_PROJET) != app.projet:
                c.problemes.append("le volume %s n'est pas du projet %s (étiquette : %r)"
                                   % (volume, app.projet, etiq.get(LABEL_PROJET)))
            else:
                c.volumes.append(volume)
        except (commandes.ErreurCommande, ValueError, IndexError, AttributeError, TypeError) as e:
            c.problemes.append("volume %s illisible : %s" % (volume, filtrer(str(e))))
    return c


# ----------------------------------------------------------------------------------------------
# Invariant 4 : comptes avant et après
# ----------------------------------------------------------------------------------------------

_RE_TABLE = re.compile(r"^[a-z_][a-z0-9_]*$")


def lire_base(app):
    """Retourne (révision de migration, {table: lignes}). Lève ErreurBase."""
    try:
        sortie = commandes.base_lire(app.conteneur_db)
    except commandes.ErreurCommande as e:
        raise ErreurBase("lecture de la base impossible : %s" % filtrer(str(e)))
    revision = None
    tables = {}
    for ligne in sortie.splitlines():
        morceaux = ligne.strip().split("|")
        if morceaux[0] == "R" and len(morceaux) == 2:
            revision = morceaux[1]
        elif morceaux[0] == "T" and len(morceaux) == 3 and _RE_TABLE.match(morceaux[1]) and morceaux[2].isdigit():
            tables[morceaux[1]] = int(morceaux[2])
    if revision is None or not tables:
        raise ErreurBase("lecture de la base incomplète (révision ou tables manquantes)")
    return revision, tables


def tables_histoire_absentes(app, tables):
    return [t for t in app.tables_histoire if t not in tables]


def comparer_comptes(app, avant, apres):
    """Retourne (baisses_histoire, autres_baisses) : listes de (table, avant, apres ou None)."""
    histoire, autres = [], []
    for t, n in sorted(avant.items()):
        a = apres.get(t)
        if a is None or a < n:
            (histoire if t in app.tables_histoire else autres).append((t, n, a))
    return histoire, autres


def lignes_comptes(app, avant, apres=None):
    """Lignes Markdown d'un tableau table par table ; baisses en gras."""
    out = ["| table | avant | après |", "|---|---:|---:|"]
    for t in sorted(set(avant) | set(apres or {})):
        a = avant.get(t)
        b = (apres or {}).get(t)
        txt_b = "—" if apres is None else ("absente" if b is None else str(b))
        baisse = apres is not None and a is not None and (b is None or b < a)
        histoire = " (histoire)" if t in app.tables_histoire else ""
        ligne = "| %s%s | %s | %s |" % (t, histoire, "—" if a is None else a, txt_b)
        if baisse:
            ligne = "| **%s%s** | **%s** | **%s** |" % (t, histoire, a, txt_b)
        out.append(ligne)
    return out


# ----------------------------------------------------------------------------------------------
# Invariant 3 : une sauvegarde relue avant chaque déploiement
# ----------------------------------------------------------------------------------------------

def _revision_sure(revision):
    return re.sub(r"[^A-Za-z0-9.-]", "x", revision)


def nom_sauvegarde(app, revision, horodatage):
    base = "%s_deploiement-%s_%s" % (app.prefixe_sauvegarde, _revision_sure(revision), horodatage)
    return base + ".dump", base + "_ecussons.tar.gz"


def _garder_en_echec(chemins):
    for c in chemins:
        if not os.path.exists(c):
            continue
        cible = c + ".echec"
        n = 1
        while os.path.exists(cible):
            n += 1
            cible = "%s.echec%d" % (c, n)
        os.rename(c, cible)


def sauvegarder(app, revision, nb_tables, image_db, horodatage, battement=None):
    """Prend la sauvegarde du §3 invariant 3. Retourne un dict (noms, tailles, entrées) ou lève ErreurBase.

    Écrit en ``.part`` puis renomme ; un contrôle qui échoue garde les fichiers en ``.echec``.
    """
    dossier = os.path.join(app.dossier, "backups")
    uid, gid = ecriture.proprietaire(app.dossier)
    ecriture.creer_dossiers(dossier, uid, gid)
    nom_dump, nom_ecussons = nom_sauvegarde(app, revision, horodatage)
    dump, ecussons = os.path.join(dossier, nom_dump), os.path.join(dossier, nom_ecussons)
    dump_part, ecussons_part = dump + ".part", ecussons + ".part"
    try:
        commandes.base_sauvegarder(app.conteneur_db, dump_part)
        taille_dump = os.path.getsize(dump_part)
        if taille_dump <= 0:
            raise ErreurBase("le dump est vide")
        toc = commandes.base_lister_dump(app.conteneur_db, dump_part)
        entrees = sum(1 for l in toc.splitlines() if "TABLE DATA" in l)
        if entrees < nb_tables:
            raise ErreurBase("le dump liste %d entrées TABLE DATA pour %d tables dans la base" % (entrees, nb_tables))
        commandes.volume_archiver(image_db, app.volume_ecussons, ecussons_part)
        if os.path.getsize(ecussons_part) <= 0:
            raise ErreurBase("l'archive des écussons est vide")
        membres = _relire_archive(ecussons_part, battement)
        if membres <= 0:
            raise ErreurBase("l'archive des écussons ne contient rien")
        taille_ecussons = os.path.getsize(ecussons_part)
    except (commandes.ErreurCommande, ErreurBase, OSError, tarfile.TarError, EOFError) as e:
        _garder_en_echec([dump_part, ecussons_part])
        detail = filtrer(str(e)) if isinstance(e, commandes.ErreurCommande) else str(e)
        raise ErreurBase("sauvegarde refusée : %s (fichiers gardés en .echec dans %s)" % (detail, dossier))
    os.replace(dump_part, dump)
    os.replace(ecussons_part, ecussons)
    for f in (dump, ecussons):
        os.chmod(f, ecriture.MODE_FICHIER)
        ecriture.appliquer_proprietaire(f, *ecriture.proprietaire(dossier))
    return {"dump": nom_dump, "taille_dump": taille_dump, "entrees_donnees": entrees, "ecussons": nom_ecussons,
            "taille_ecussons": taille_ecussons, "membres_ecussons": membres}


def _relire_archive(chemin, battement=None):
    """Relit entièrement l'archive (vérifie la somme de contrôle de gzip) ; retourne le nombre de membres."""
    n = 0
    with tarfile.open(chemin, "r:gz") as tf:
        for m in tf:
            n += 1
            if m.isfile():
                f = tf.extractfile(m)
                while f.read(1 << 20):
                    if battement:
                        battement()
    return n


# ----------------------------------------------------------------------------------------------
# Invariant 6 : la purge ne descend jamais sous trois
# ----------------------------------------------------------------------------------------------

def _motif(app):
    return re.compile(r"^%s_deploiement-(.+)_(\d{8}-\d{6})(\.dump|_ecussons\.tar\.gz)$" % re.escape(app.prefixe_sauvegarde))


def sauvegardes_deployeur(app):
    """{(révision, horodatage): {'.dump': nom, '_ecussons.tar.gz': nom}} pour la seule famille du déployeur."""
    dossier = os.path.join(app.dossier, "backups")
    groupes = {}
    try:
        noms = os.listdir(dossier)
    except FileNotFoundError:
        return groupes
    m = _motif(app)
    for nom in noms:
        r = m.match(nom)
        if r:
            groupes.setdefault((r.group(1), r.group(2)), {})[r.group(3)] = nom
    return groupes


def purger(app, garder):
    """Garde les ``max(3, garder)`` sauvegardes les plus récentes du déployeur ; retourne les noms retirés."""
    garder = max(3, int(garder))
    groupes = sauvegardes_deployeur(app)
    ordre = sorted(groupes, key=lambda k: (k[1], k[0]), reverse=True)
    retires = []
    dossier = os.path.join(app.dossier, "backups")
    for cle in ordre[garder:]:
        for nom in sorted(groupes[cle].values()):
            os.remove(os.path.join(dossier, nom))
            retires.append(nom)
    return retires


def dernieres_sauvegardes(app, par_famille=3):
    """Les trois dernières sauvegardes de chaque famille de ``backups/`` : {famille: [(nom, mtime, taille)]}."""
    dossier = os.path.join(app.dossier, "backups")
    re_nom = re.compile(r"^%s_([a-z]+)-.*\.dump$" % re.escape(app.prefixe_sauvegarde))
    familles = {}
    try:
        noms = os.listdir(dossier)
    except (FileNotFoundError, PermissionError):
        return familles
    for nom in noms:
        r = re_nom.match(nom)
        if not r:
            continue
        try:
            st = os.stat(os.path.join(dossier, nom))
        except OSError:
            continue
        familles.setdefault(r.group(1), []).append((nom, st.st_mtime, st.st_size))
    return {f: sorted(v, key=lambda x: x[1], reverse=True)[:par_famille] for f, v in sorted(familles.items())}


def nom_lisible(octets):
    return compterendu.taille(octets)
