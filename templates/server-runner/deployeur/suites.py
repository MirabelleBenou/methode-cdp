"""Les suites : des fichiers HTML autoportants servis tels quels. Aucun redémarrage.

Le fichier servi ne manque jamais : chaque remplacement passe par un fichier temporaire du même dossier et
``os.replace``. L'ancien fichier se garde en ``<nom>.prec<extension>``.
"""

import os
import urllib.parse

from . import ecriture, reseau
from .compterendu import REUSSI
from .contexte import Refus
from .filtre import filtrer

TAILLE_MAX = 64 << 20


def nom_prec(fichier):
    base, ext = os.path.splitext(fichier)
    return "%s.prec%s" % (base, ext)


def chemins(suite):
    return os.path.join(suite.dossier, suite.fichier), os.path.join(suite.dossier, nom_prec(suite.fichier))


def url_fichier(cfg, suite, commit):
    return "https://%s/%s/%s/%s" % (cfg.hote_fichiers_bruts, suite.depot, commit, urllib.parse.quote(suite.chemin))


def _sha_ou_none(chemin):
    try:
        return ecriture.sha256_fichier(chemin)
    except FileNotFoundError:
        return None


def deployer(ctx, compte, ordre):
    cfg = ctx.cfg
    suite = cfg.suites[ordre.champs["suite"]]
    commit = ordre.champs["commit"]
    attendu = ordre.champs["sha256"]
    servi, prec = chemins(suite)
    if not os.path.isdir(suite.dossier):
        raise Refus("le dossier de la suite n'existe pas : %s" % suite.dossier)
    uid, gid = ecriture.proprietaire(suite.dossier)
    url = url_fichier(cfg, suite, commit)
    hotes = reseau.hotes_permis(cfg)
    temporaire = os.path.join(suite.dossier, ".dep-%s.tmp" % ordre.id)
    avant = _sha_ou_none(servi)
    try:
        try:
            taille, somme = reseau.telecharger(url, hotes, temporaire, sha256=attendu, taille_max=TAILLE_MAX,
                                               battement=ctx.tick)
        except reseau.ErreurReseau as e:
            raise Refus("téléchargement refusé : %s ; le fichier servi est intact" % filtrer(str(e)))
        os.chmod(temporaire, ecriture.MODE_FICHIER)
        ecriture.appliquer_proprietaire(temporaire, uid, gid)
        if os.path.exists(servi):
            copie = os.path.join(suite.dossier, ".dep-%s.prec.tmp" % ordre.id)
            try:
                with open(servi, "rb") as src, open(copie, "wb") as dst:
                    while True:
                        bloc = src.read(1 << 20)
                        if not bloc:
                            break
                        dst.write(bloc)
                    dst.flush()
                    os.fsync(dst.fileno())
                os.chmod(copie, ecriture.MODE_FICHIER)
                ecriture.appliquer_proprietaire(copie, uid, gid)
                os.replace(copie, prec)
            finally:
                if os.path.exists(copie):
                    os.remove(copie)
        os.replace(temporaire, servi)
    finally:
        if os.path.exists(temporaire):
            os.remove(temporaire)
    apres = _sha_ou_none(servi)
    if apres != attendu:
        raise Refus("contrôle final en échec : sha256 du fichier servi %s, attendu %s" % (apres, attendu))
    s = compte.section("Résultat")
    s.append("- suite : %s (%s)" % (suite.nom, servi))
    s.append("- source : %s" % url)
    s.append("- taille : %d octets" % taille)
    s.append("- sha256 avant : %s" % (avant or "— (aucun fichier servi)"))
    s.append("- sha256 servi : %s (conforme à l'ordre)" % apres)
    s.append("- ancien fichier gardé : %s" % (prec if avant else "— (rien à garder)"))
    return REUSSI


def revenir(ctx, compte, ordre):
    suite = ctx.cfg.suites[ordre.champs["cible"]]
    servi, prec = chemins(suite)
    if not os.path.isfile(prec):
        raise Refus("aucun fichier précédent (%s) : rien à restaurer" % nom_prec(suite.fichier))
    if not os.path.isfile(servi):
        raise Refus("aucun fichier servi (%s) : retour impossible" % suite.fichier)
    uid, gid = ecriture.proprietaire(suite.dossier)
    avant_servi, avant_prec = _sha_ou_none(servi), _sha_ou_none(prec)
    copie = os.path.join(suite.dossier, ".dep-%s.swap.tmp" % ordre.id)
    try:
        with open(servi, "rb") as src, open(copie, "wb") as dst:
            while True:
                bloc = src.read(1 << 20)
                if not bloc:
                    break
                dst.write(bloc)
            dst.flush()
            os.fsync(dst.fileno())
        os.chmod(copie, ecriture.MODE_FICHIER)
        ecriture.appliquer_proprietaire(copie, uid, gid)
        os.replace(prec, servi)      # le servi n'est jamais absent
        os.replace(copie, prec)      # l'ancien servi devient le précédent
    finally:
        if os.path.exists(copie):
            os.remove(copie)
    s = compte.section("Résultat")
    s.append("- suite : %s" % suite.nom)
    s.append("- sha256 servi avant : %s ; après : %s" % (avant_servi, _sha_ou_none(servi)))
    s.append("- sha256 du précédent avant : %s ; après : %s" % (avant_prec, _sha_ou_none(prec)))
    return REUSSI
