"""Les actions sur l'application (le projet Compose déployé) : adopter, deployer-application, revenir.

Le service de la base n'est jamais touché : seuls ``build`` et ``up -d --no-deps`` du service applicatif modifient
des conteneurs. La base ne se restaure jamais ici.
"""

import os
import shutil

from . import archives, base, commandes, compterendu, ecriture, reseau
from .compterendu import ECHEC_ARRET, ECHEC_REVENU, REUSSI
from .contexte import Refus
from .filtre import filtrer

GO = 1 << 30


def place_libre_go(chemin):
    return shutil.disk_usage(chemin).free / float(GO)


def _erreur_commande(compte, quoi, e):
    compte.ligne("Erreur", "%s : %s" % (quoi, filtrer(str(e))))


compterendu_filtre = filtrer


# ----------------------------------------------------------------------------------------------
# Étape 1 : préconditions communes
# ----------------------------------------------------------------------------------------------

def verifier_projet(ctx, compte):
    """Invariant 2 : le bon projet ou rien. Retourne le contrôle ; lève Refus sinon."""
    app = ctx.cfg.application
    ctrl = base.controler_projet(app)
    lignes = compte.section("Contrôles du projet")
    lignes.append("- projet : %s ; dossier : %s" % (app.projet, app.dossier))
    for c in ctrl.conteneurs:
        lignes.append("- conteneur %s (service %s) : %s %s" % (c["nom"], c["service"], c["etat"], c["sante"]))
    if ctrl.problemes:
        for p in ctrl.problemes:
            lignes.append("- **problème** : %s" % p)
        raise Refus("contrôle du projet en échec : " + " ; ".join(ctrl.problemes))
    lignes.append("- étiquettes, volumes et montage de la base : conformes")
    return ctrl


def preparer_miroir(ctx):
    """Le miroir de l'application (toutes les branches) est cloné s'il manque, puis mis à jour."""
    chemin = ctx.registre.chemin("miroir-application")
    acces = ctx.acces_application()
    try:
        if not os.path.isdir(os.path.join(chemin, "objects")):
            commandes.git_cloner_miroir(acces, ctx.cfg.application.depot_url, chemin)
        commandes.git_recuperer_miroir(acces, chemin)
    except commandes.ErreurCommande as e:
        raise Refus("miroir de l'application inaccessible : %s" % compterendu_filtre(str(e)))
    return chemin


def lire_version_archive(arc):
    if "VERSION" not in arc.fichiers:
        return None
    return arc.lire("VERSION").read().decode("utf-8", "replace").strip()


def extraire_archive(ctx, miroir, commit, travail):
    if not commandes.git_commit_existe(miroir, commit):
        raise Refus("le commit %s n'existe pas dans le miroir de l'application" % commit)
    chemin = os.path.join(travail, "archive.tar")
    try:
        commandes.git_archive(miroir, commit, chemin)
        return archives.Archive(chemin)
    except commandes.ErreurCommande as e:
        raise Refus("archive du commit impossible : %s" % compterendu_filtre(str(e)))
    except archives.ArchiveInvalide as e:
        raise Refus("archive du commit refusée : %s" % e)


def controler_protection(app, arc):
    trouves = [c for c in sorted(arc.fichiers) if archives.est_protege(c, app.chemins_proteges)]
    if trouves:
        raise Refus("l'archive contient des chemins protégés : %s" % ", ".join(trouves[:10]))


def _sante_info(app):
    obj, err = reseau.lire_json(app.url_sante)
    if isinstance(obj, dict) and "version" in obj:
        return str(obj["version"])
    return None


# ----------------------------------------------------------------------------------------------
# adopter
# ----------------------------------------------------------------------------------------------

def adopter(ctx, compte, ordre):
    app = ctx.cfg.application
    reg = ctx.registre
    commit = ordre.champs["commit"]
    etat = reg.application()
    if etat.get("servi"):
        raise Refus("un commit servi est déjà connu (%s) : adopter ne se joue qu'une fois" % etat["servi"]["commit"])
    verifier_projet(ctx, compte)
    miroir = preparer_miroir(ctx)
    travail = reg.travail(ordre.id)
    try:
        arc = extraire_archive(ctx, miroir, commit, travail)
        with arc:
            controler_protection(app, arc)
            version = lire_version_archive(arc)
            if not version:
                raise Refus("l'archive ne contient pas de fichier VERSION")
            ecarts = archives.comparer(arc, app.dossier)
            if ecarts:
                lignes = compte.section("Écarts")
                lignes.extend("- %s : %s" % e for e in ecarts[:50])
                if len(ecarts) > 50:
                    lignes.append("- … et %d autres" % (len(ecarts) - 50))
                raise Refus("%d fichier(s) du dossier diffèrent de l'archive du commit : rien n'est retenu" % len(ecarts))
            hors, total = archives.fichiers_hors_archive(app.dossier, set(arc.fichiers), app.chemins_proteges)
            try:
                revision, tables = base.lire_base(app)
            except base.ErreurBase as e:
                raise Refus(str(e))
            manifeste = arc.manifeste()
            ecriture.ecrire_json(reg.chemin_manifeste(commit), {"commit": commit, "fichiers": manifeste})
            shutil.copyfile(arc.chemin, reg.chemin_archive(commit) + ".tmp")
            os.replace(reg.chemin_archive(commit) + ".tmp", reg.chemin_archive(commit))
        etat = {"servi": {"commit": commit, "version": version, "revision": revision, "depuis": compterendu.horodatage()},
                "precedent": None, "historique": [commit]}
        reg.enregistrer_application(etat)
    finally:
        shutil.rmtree(travail, ignore_errors=True)
    s = compte.section("Résultat")
    s.append("- commit adopté : %s (version %s)" % (commit, version))
    s.append("- %d fichiers identiques à l'archive (sha256 et bit d'exécution)" % len(manifeste))
    s.append("- révision de migration : %s" % revision)
    vs = _sante_info(app)
    s.append("- version annoncée par l'application : %s" % (vs or "illisible"))
    if vs and vs != version:
        s.append("- **attention** : la version annoncée diffère du fichier VERSION de l'archive")
    s.append("- fichiers du dossier hors archive (laissés, jamais touchés) : %d" % total)
    s.extend("  - %s" % f for f in hors[:100])
    if total > len(hors[:100]):
        s.append("  - … et %d autres" % (total - len(hors[:100])))
    return REUSSI


# ----------------------------------------------------------------------------------------------
# deployer-application (et revenir : mêmes étapes avec le commit précédent)
# ----------------------------------------------------------------------------------------------

def _remettre_fichiers(ctx, compte, commit_servi, manifeste_nouveau):
    """Remet les fichiers du commit servi. Retourne True si tout est en place."""
    app = ctx.cfg.application
    reg = ctx.registre
    try:
        uid, gid = ecriture.proprietaire(app.dossier)
        with archives.Archive(reg.chemin_archive(commit_servi)) as ancien:
            stats = archives.poser(ancien, app.dossier, manifeste_nouveau, app.chemins_proteges, uid, gid, ctx.tick)
        compte.ligne("Remise en place", "- fichiers du commit servi remis : %d réécrits, %d retirés"
                     % (len(stats["poses"]), len(stats["retires"])))
        return True
    except Exception as e:  # noqa: BLE001 - la remise est le dernier recours, on rend compte
        compte.ligne("Remise en place", "- **remise des fichiers impossible** : %s" % e)
        return False


def _attendre_sante(ctx, compte, version, depuis):
    """Étape 7. Retourne (ok, raison)."""
    app = ctx.cfg.application
    limite = ctx.monotone() + app.delai_sante_s
    derniere = "aucune réponse"
    ok = False
    while True:
        obj, err = reseau.lire_json(app.url_sante)
        if isinstance(obj, dict) and str(obj.get("version")) == version:
            ok = True
            break
        derniere = ("version annoncée : %r" % obj.get("version")) if isinstance(obj, dict) else (err or "réponse illisible")
        if ctx.monotone() >= limite:
            break
        ctx.dormir(app.intervalle_sante_s)
        ctx.tick()
    raison = None
    try:
        logs = commandes.compose_logs(app.projet, app.dossier, app.fichier_compose, app.service_app, depuis)
        compte.journal_app = compterendu.lignes_utiles(logs)
        mauvaises = [l for l in logs.splitlines() if "Échec" in l or "Traceback" in l]
        if mauvaises:
            raison = "le journal de l'application contient : %s" % compterendu_filtre(mauvaises[0].strip()[:200])
    except commandes.ErreurCommande as e:
        raison = "journal de l'application illisible : %s" % compterendu_filtre(str(e))
        ok = False
    if not ok:
        return False, "santé non obtenue en %s s (%s)" % (app.delai_sante_s, derniere)
    if raison:
        return False, raison
    return True, None


def _build_up(ctx, compte, etape):
    app = ctx.cfg.application
    try:
        commandes.compose_build(app.projet, app.dossier, app.fichier_compose, app.service_app)
    except commandes.ErreurCommande as e:
        _erreur_commande(compte, "%s : build en échec" % etape, e)
        return "build", None
    depuis = compterendu.horodatage()
    try:
        commandes.compose_up(app.projet, app.dossier, app.fichier_compose, app.service_app)
    except commandes.ErreurCommande as e:
        _erreur_commande(compte, "%s : up en échec" % etape, e)
        return "up", depuis
    return None, depuis


def _arreter_file(ctx, compte, ordre_id, raison, incertain=True):
    """Arrête la file. Par défaut l'état est incertain : le compte rendu le dit et ``application.json`` reçoit un champ
    ``incertain`` (ordre, raison, date), effacé par le prochain succès ; tant qu'il est posé, ``revenir`` est refusé."""
    date = compterendu.horodatage()
    ctx.registre.arreter(ctx.file, ordre_id, raison, date)
    compte.ligne("File arrêtée", "- la file %s est arrêtée : %s" % (ctx.file, raison))
    if incertain:
        etat = ctx.registre.application()
        etat["incertain"] = {"ordre": ordre_id, "raison": raison, "date": date}
        ctx.registre.enregistrer_application(etat)
        compte.ligne("File arrêtée", "- état réel à constater par `etat` : le déployeur ne sait pas ce qui tourne ; "
                                     "`revenir` est refusé jusqu'au prochain déploiement réussi")
    compte.decider("la file est arrêtée ; vérifier l'état réel (ordre `etat`) puis jouer `reprendre-file` avec un `go`")
    ctx.log("file arrêtée : %s" % raison)


def _promouvoir(ctx, etat, servi, commit, version, revision, manifeste_nouveau, arc):
    """Le nouveau commit devient « servi » (version, révision, manifeste et archive gardés), l'ancien « précédent »."""
    reg = ctx.registre
    ancien = dict(servi)
    nouveau = {"commit": commit, "version": version, "revision": revision, "depuis": compterendu.horodatage()}
    ecriture.ecrire_json(reg.chemin_manifeste(commit), {"commit": commit, "fichiers": manifeste_nouveau})
    shutil.copyfile(arc.chemin, reg.chemin_archive(commit) + ".tmp")
    os.replace(reg.chemin_archive(commit) + ".tmp", reg.chemin_archive(commit))
    etat["servi"] = nouveau
    if commit != ancien["commit"] or not etat.get("precedent"):
        etat["precedent"] = ancien
    hist = [commit] + [c for c in etat.get("historique", []) if c != commit]
    etat["historique"] = hist
    reg.enregistrer_application(etat)
    reg.garder_archives(etat)


def _arret_nouveau_en_place(ctx, compte, ordre_id, etat, servi, commit, version, revision, manifeste_nouveau, arc, raison):
    """Arrêt de la file alors que les fichiers et le conteneur du nouveau commit restent en place : le registre suit le
    disque (étape 10), puis la file s'arrête."""
    _promouvoir(ctx, etat, servi, commit, version, revision, manifeste_nouveau, arc)
    compte.ligne("Résumé", "- le commit `%s` est en place mais la file est arrêtée (version %s, révision %s)"
                 % (commit, version, revision))
    _arreter_file(ctx, compte, ordre_id, raison, incertain=False)


def _noms_sauvegardes_utiles(app):
    fam = base.dernieres_sauvegardes(app, 1)
    return {f: v[0][0] for f, v in fam.items() if f in ("deploiement", "rev")}


def deployer(ctx, compte, ordre_id, commit, version, controle=None):
    app = ctx.cfg.application
    reg = ctx.registre
    etat = reg.application()
    servi = etat.get("servi")
    if not servi:
        raise Refus("aucun commit servi connu : jouer `adopter` d'abord")
    s = compte.section("Résumé")
    s.append("- version servie avant : %s (commit %s)" % (servi["version"], servi["commit"]))
    s.append("- cible : version %s (commit %s)" % (version, commit))

    # -- étape 1 : préconditions -----------------------------------------------------------------
    compte.etape("1 préconditions")
    ctrl = controle if controle is not None else verifier_projet(ctx, compte)
    libre = place_libre_go(app.dossier)
    s.append("- place libre du dossier Compose : %.1f Go (minimum %s Go)" % (libre, app.place_min_deploiement_go))
    if libre < app.place_min_deploiement_go:
        raise Refus("place insuffisante dans le dossier Compose : %.1f Go libres pour %s Go requis"
                    % (libre, app.place_min_deploiement_go))
    if not os.path.isfile(reg.chemin_archive(servi["commit"])) or reg.manifeste(servi["commit"]) is None:
        raise Refus("archive ou manifeste du commit servi introuvables dans l'état du déployeur")
    miroir = preparer_miroir(ctx)
    travail = reg.travail(ordre_id)
    try:
        arc = extraire_archive(ctx, miroir, commit, travail)
        with arc:
            v_archive = lire_version_archive(arc)
            if v_archive != version:
                raise Refus("le fichier VERSION de l'archive (%r) ne correspond pas à l'ordre (%r)" % (v_archive, version))
            if app.fichier_compose not in arc.fichiers:
                raise Refus("l'archive ne contient pas le fichier %s" % app.fichier_compose)
            controler_protection(app, arc)
            return _suite_deploiement(ctx, compte, ordre_id, commit, version, servi, etat, arc, ctrl.image_db)
    finally:
        shutil.rmtree(travail, ignore_errors=True)


def _suite_deploiement(ctx, compte, ordre_id, commit, version, servi, etat, arc, image):
    app = ctx.cfg.application
    reg = ctx.registre
    manifeste_servi = reg.manifeste(servi["commit"])

    # -- étape 2 : comptes et révision avant -----------------------------------------------------
    compte.etape("2 comptes avant")
    try:
        rev_avant, avant = base.lire_base(app)
    except base.ErreurBase as e:
        raise Refus(str(e))
    absentes = base.tables_histoire_absentes(app, avant)
    if absentes:
        raise Refus("tables d'histoire absentes de la base : %s" % ", ".join(absentes))
    compte.ligne("Résumé", "- révision de migration avant : %s" % rev_avant)

    # -- étape 3 : sauvegarde --------------------------------------------------------------------
    compte.etape("3 sauvegarde")
    stamp = ctx.maintenant().strftime("%Y%m%d-%H%M%S")
    try:
        sauv = base.sauvegarder(app, rev_avant, len(avant), image, stamp, ctx.tick)
    except base.ErreurBase as e:
        raise Refus(str(e))
    sl = compte.section("Sauvegarde")
    sl.append("- %s (%s ; %d entrées TABLE DATA pour %d tables)" % (sauv["dump"], compterendu.taille(sauv["taille_dump"]),
                                                                  sauv["entrees_donnees"], len(avant)))
    sl.append("- %s (%s ; %d membres relus sans erreur)" % (sauv["ecussons"], compterendu.taille(sauv["taille_ecussons"]),
                                                          sauv["membres_ecussons"]))

    # -- étape 4 : pose des fichiers -------------------------------------------------------------
    compte.etape("4 pose des fichiers")
    uid, gid = ecriture.proprietaire(app.dossier)
    manifeste_nouveau = arc.manifeste()
    try:
        stats = archives.poser(arc, app.dossier, manifeste_servi, app.chemins_proteges, uid, gid, ctx.tick)
    except Exception as e:  # noqa: BLE001
        compte.ligne("Erreur", "pose des fichiers en échec : %s" % e)
        ok = _remettre_fichiers(ctx, compte, servi["commit"], manifeste_nouveau)
        if not ok:
            _arreter_file(ctx, compte, ordre_id, "la remise des fichiers du commit servi a échoué")
            return ECHEC_ARRET
        compte.decider("l'ordre a échoué à la pose des fichiers ; les fichiers du commit servi sont remis ; "
                       "corriger la cause avant de rejouer un ordre")
        return ECHEC_REVENU
    inconnus, total_inconnus = archives.fichiers_hors_archive(
        app.dossier, set(manifeste_nouveau) | set(manifeste_servi), app.chemins_proteges)
    fl = compte.section("Fichiers")
    fl.append("- posés ou remplacés : %d ; inchangés : %d ; retirés : %d" % (len(stats["poses"]), len(stats["inchanges"]),
                                                                          len(stats["retires"])))
    for r in stats["retires"][:50]:
        fl.append("  - retiré : %s" % r)
    if stats["ecrases_inconnus"]:
        fl.append("- fichiers existants inconnus du manifeste servi et remplacés par l'archive : %s"
                  % ", ".join(stats["ecrases_inconnus"][:20]))
    fl.append("- fichiers inconnus laissés intacts : %d" % total_inconnus)
    fl.extend("  - %s" % f for f in inconnus[:50])

    # -- étapes 5 et 6 : build puis up -----------------------------------------------------------
    compte.etape("5 build")
    quoi_echec, depuis = _build_up(ctx, compte, "étape 5-6")
    if quoi_echec == "build":
        ok = _remettre_fichiers(ctx, compte, servi["commit"], manifeste_nouveau)
        if not ok:
            _arreter_file(ctx, compte, ordre_id, "la remise des fichiers du commit servi a échoué après un build en échec")
            return ECHEC_ARRET
        compte.ligne("Résumé", "- le build a échoué ; aucun conteneur n'a changé ; la version %s reste servie (%s)"
                     % (servi["version"], _sante_info(app) or "santé illisible"))
        compte.decider("le build de la version %s a échoué ; lire l'erreur ci-dessus avant de rejouer" % version)
        return ECHEC_REVENU

    # -- étape 7 : santé -------------------------------------------------------------------------
    ok_sante = False
    raison = None
    if quoi_echec is None:
        compte.etape("6 up ; 7 santé")
        ok_sante, raison = _attendre_sante(ctx, compte, version, depuis)
    else:
        raison = "`up` en échec"
        _journal_app(ctx, compte, depuis)
    if not ok_sante:
        return _echec_apres_up(ctx, compte, ordre_id, etat, servi, (commit, version, arc), manifeste_nouveau, rev_avant, avant,
                               raison)

    # -- étape 9 : comptes après -----------------------------------------------------------------
    compte.etape("9 comptes après")
    try:
        rev_apres, apres = base.lire_base(app)
    except base.ErreurBase as e:
        compte.ligne("Erreur", str(e))
        _arreter_file(ctx, compte, ordre_id, "comptes après impossibles à lire alors que la santé est bonne")
        return ECHEC_ARRET
    cl = compte.section("Comptes des tables")
    cl.extend(base.lignes_comptes(app, avant, apres))
    compte.ligne("Résumé", "- révision de migration après : %s%s" % (rev_apres, "" if rev_apres != rev_avant else " (inchangée)"))
    histoire, autres = base.comparer_comptes(app, avant, apres)
    if autres:
        cl.append("")
        cl.append("Baisses rapportées (tables hors histoire) : " + ", ".join("**%s** %s → %s" % (t, a, b if b is not None else "absente") for t, a, b in autres))
    if histoire:
        _arret_nouveau_en_place(ctx, compte, ordre_id, etat, servi, commit, version, rev_apres, manifeste_nouveau, arc,
                                "une table d'histoire a baissé : " + ", ".join(
                                    "%s %s → %s" % (t, a, b if b is not None else "absente") for t, a, b in histoire))
        compte.decider("des lignes ont disparu d'une table d'histoire alors que la santé est bonne : "
                       "comparer avec la sauvegarde %s avant toute autre action" % sauv["dump"])
        return ECHEC_ARRET

    # -- étape 10 : succès -----------------------------------------------------------------------
    compte.etape("10 succès")
    etat.pop("incertain", None)
    _promouvoir(ctx, etat, servi, commit, version, rev_apres, manifeste_nouveau, arc)
    retires = base.purger(app, app.sauvegardes_garder)
    sl.append("- sauvegardes du déployeur retirées par la purge (on garde au moins %d) : %s"
              % (max(3, int(app.sauvegardes_garder)), ", ".join(retires) if retires else "aucune"))
    compte.ligne("Résumé", "- version servie après : %s (commit %s) ; santé : %s" % (version, commit, "bonne"))
    return REUSSI


def _journal_app(ctx, compte, depuis):
    app = ctx.cfg.application
    try:
        logs = commandes.compose_logs(app.projet, app.dossier, app.fichier_compose, app.service_app, depuis)
        compte.journal_app = compterendu.lignes_utiles(logs)
    except commandes.ErreurCommande:
        pass


def _echec_apres_up(ctx, compte, ordre_id, etat, servi, nouveau, manifeste_nouveau, rev_avant, avant, raison):
    """Étape 8 : échec après l'étape 6."""
    app = ctx.cfg.application
    commit, version, arc = nouveau
    compte.etape("8 échec après up : %s" % raison)
    compte.ligne("Erreur", "- %s" % raison)
    try:
        rev_now, _ = base.lire_base(app)
    except base.ErreurBase as e:
        compte.ligne("Erreur", "- révision de migration illisible : %s" % e)
        _arreter_file(ctx, compte, ordre_id, "échec après le démarrage et révision de migration illisible : aucun retour")
        _noter_sauvegardes(compte, app)
        return ECHEC_ARRET
    if rev_now != rev_avant:
        compte.ligne("Erreur", "- la révision de migration a changé (%s → %s) : aucun retour automatique" % (rev_avant, rev_now))
        _arret_nouveau_en_place(ctx, compte, ordre_id, etat, servi, commit, version, rev_now, manifeste_nouveau, arc,
                                "échec après une migration (%s → %s)" % (rev_avant, rev_now))
        _noter_sauvegardes(compte, app)
        return ECHEC_ARRET
    compte.ligne("Retour automatique", "- révision de migration inchangée (%s) : retour au commit servi" % rev_now)
    if not _remettre_fichiers(ctx, compte, servi["commit"], manifeste_nouveau):
        _arreter_file(ctx, compte, ordre_id, "retour automatique impossible (fichiers)")
        return ECHEC_ARRET
    quoi, depuis = _build_up(ctx, compte, "retour automatique")
    if quoi:
        _arreter_file(ctx, compte, ordre_id, "retour automatique en échec (%s)" % quoi)
        return ECHEC_ARRET
    ok, raison2 = _attendre_sante(ctx, compte, servi["version"], depuis)
    if not ok:
        compte.ligne("Retour automatique", "- santé de l'ancienne version non obtenue : %s" % raison2)
        _arreter_file(ctx, compte, ordre_id, "l'ancienne version ne répond pas après le retour")
        return ECHEC_ARRET
    try:
        _, apres = base.lire_base(app)
        histoire, _ = base.comparer_comptes(app, avant, apres)
    except base.ErreurBase:
        histoire = [("?", 0, None)]
    if histoire:
        _arreter_file(ctx, compte, ordre_id, "après le retour, une table d'histoire a baissé ou n'est pas lisible")
        _noter_sauvegardes(compte, app)
        return ECHEC_ARRET
    compte.ligne("Retour automatique", "- ancienne version %s de nouveau servie, santé bonne, comptes d'histoire intacts"
                 % servi["version"])
    compte.decider("la version demandée n'a pas démarré (%s) ; l'ancienne version est revenue ; "
                   "corriger avant de rejouer" % raison)
    return ECHEC_REVENU


def _noter_sauvegardes(compte, app):
    noms = _noms_sauvegardes_utiles(app)
    compte.decider("la base n'est jamais restaurée par le déployeur ; restauration manuelle, avec la sauvegarde "
                   "du déploiement `%s` et la dernière sauvegarde avant migration `%s`"
                   % (noms.get("deploiement", "?"), noms.get("rev", "?")))


# ----------------------------------------------------------------------------------------------
# revenir (application)
# ----------------------------------------------------------------------------------------------

def revenir(ctx, compte, ordre):
    app = ctx.cfg.application
    etat = ctx.registre.application()
    prec = etat.get("precedent")
    inc = etat.get("incertain")
    if inc:
        raise Refus("l'état du déployeur est incertain depuis l'ordre %s (%s, %s) : constater l'état réel par `etat`, "
                    "puis déployer un commit pour rétablir l'état connu ; `revenir` est refusé en attendant"
                    % (inc.get("ordre", "?"), inc.get("raison", "?"), inc.get("date", "?")))
    if not etat.get("servi") or not prec:
        raise Refus("aucun commit précédent connu : rien à restaurer")
    ctrl = verifier_projet(ctx, compte)
    try:
        rev_now, _ = base.lire_base(app)
    except base.ErreurBase as e:
        raise Refus(str(e))
    if rev_now != prec.get("revision"):
        noms = _noms_sauvegardes_utiles(app)
        raise Refus("une migration a été appliquée depuis (révision %s, celle du précédent : %s) : la base ne se "
                    "restaure pas par le déployeur ; procédure de restauration manuelle de l'exploitation avec la "
                    "sauvegarde `%s` (dernière avant migration : `%s`)"
                    % (rev_now, prec.get("revision"), noms.get("deploiement", "?"), noms.get("rev", "?")))
    compte.ligne("Résumé", "- retour demandé vers le commit précédent %s (version %s)" % (prec["commit"], prec["version"]))
    return deployer(ctx, compte, ordre.id, prec["commit"], prec["version"], controle=ctrl)
