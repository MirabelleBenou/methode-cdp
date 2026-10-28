"""L'action ``etat`` : lecture seule, toujours acceptée, même sur une file arrêtée."""

import datetime
import os
import shutil

from . import base, ecriture, reseau, suites
from .filtre import filtrer
from .compterendu import REUSSI, taille

GO = 1 << 30


def _libre(chemin):
    try:
        return "%.1f Go libres" % (shutil.disk_usage(chemin).free / float(GO))
    except OSError as e:
        return "illisible (%s)" % e


def _sha(chemin):
    try:
        return ecriture.sha256_fichier(chemin)
    except FileNotFoundError:
        return "absent"
    except OSError as e:
        return "illisible (%s)" % e


def etat(ctx, compte, ordre):
    cfg = ctx.cfg
    app = cfg.application
    reg = ctx.registre

    # application : santé, conteneurs, contrôles du projet
    s = compte.section("Application")
    obj, err = reseau.lire_json(app.url_sante)
    if isinstance(obj, dict) and "version" in obj:
        s.append("- version servie (santé) : %s" % obj["version"])
    else:
        s.append("- version servie (santé) : illisible (%s)" % filtrer(err or "réponse inattendue"))
    ctrl = base.controler_projet(app)
    for c in ctrl.conteneurs:
        s.append("- conteneur %s (service %s) : %s %s" % (c["nom"], c["service"], c["etat"], c["sante"]))
    if ctrl.problemes:
        for p in ctrl.problemes:
            s.append("- **contrôle du projet en échec** : %s" % p)
    else:
        s.append("- contrôle du projet : conforme (étiquettes, volumes, montage de la base)")
    etat_app = reg.application()
    servi, prec = etat_app.get("servi"), etat_app.get("precedent")
    if servi:
        s.append("- commit servi selon le déployeur : %s (version %s, révision %s, depuis %s)"
                 % (servi["commit"], servi["version"], servi["revision"], servi.get("depuis", "?")))
    else:
        s.append("- commit servi selon le déployeur : inconnu (jouer `adopter`)")
    if etat_app.get("incertain"):
        inc = etat_app["incertain"]
        s.append("- ÉTAT INCERTAIN depuis l'ordre %s (%s, %s) : constater ce qui tourne ; `revenir` est refusé jusqu'au "
                 "prochain déploiement réussi" % (inc.get("ordre", "?"), inc.get("raison", "?"), inc.get("date", "?")))
    if prec:
        s.append("- commit précédent : %s (version %s, révision %s)" % (prec["commit"], prec["version"], prec["revision"]))

    # base
    b = compte.section("Base")
    if ctrl.ok:
        try:
            revision, tables = base.lire_base(app)
            b.append("- révision de migration : %s" % revision)
            b.append("")
            b.extend(base.lignes_comptes(app, tables))
        except base.ErreurBase as e:
            b.append("- lecture impossible : %s" % e)
    else:
        b.append("- non lue : le contrôle du projet a échoué")

    # place libre
    p = compte.section("Place libre")
    p.append("- dossier Compose (%s) : %s" % (app.dossier, _libre(app.dossier)))
    for nom, z in sorted(cfg.zones.items()):
        p.append("- zone %s (%s) : %s" % (nom, z.chemin, _libre(z.chemin)))

    # sauvegardes
    sv = compte.section("Sauvegardes (trois dernières de chaque famille)")
    familles = base.dernieres_sauvegardes(app)
    if not familles:
        sv.append("- aucune")
    for fam, liste in familles.items():
        sv.append("- famille %s :" % fam)
        for nom, mtime, t in liste:
            date = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            sv.append("  - %s (%s, %s)" % (nom, date, taille(t)))

    # suites
    su = compte.section("Suites")
    for nom, suite in sorted(cfg.suites.items()):
        servi_p, prec_p = suites.chemins(suite)
        su.append("- %s : sha256 servi %s ; sha256 %s %s" % (nom, _sha(servi_p), os.path.basename(prec_p), _sha(prec_p)))

    # files
    f = compte.section("Files")
    for file in ("deploiement", "fichiers"):
        a = reg.arret(file)
        f.append("- %s : %s" % (file, "ARRÊTÉE depuis l'ordre %s (%s) : %s" % (a["ordre"], a["date"], a["raison"]) if a else "en marche"))

    # ordres des 7 derniers jours
    o = compte.section("Ordres joués (7 derniers jours)")
    limite = ctx.maintenant() - datetime.timedelta(days=7)
    joues = []
    for file in ("deploiement", "fichiers"):
        for oid, e in reg.journal(file).items():
            debut = e.get("debut", "")
            try:
                d = datetime.datetime.strptime(debut, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                continue
            if d >= limite:
                joues.append((oid, file, e.get("statut", "?"), debut))
    for oid, file, statut, debut in sorted(joues):
        o.append("- %s (%s) : %s, commencé le %s" % (oid, file, statut, debut))
    if not joues:
        o.append("- aucun")
    return REUSSI
