"""Un passage d'une file : verrou, synchronisation du dépôt d'ordres, ordres interrompus, ordres neufs par id."""

import os
import traceback

from . import (action_etat, application, compterendu, ecriture, fichiers, ordres, registre as reg_mod, suites)
from .compterendu import (ECHEC_ARRET, EN_COURS, INTERROMPU, REFUSE, REUSSI, Compte)
from .contexte import Contexte, Refus
from .depot import DepotOrdres
from .filtre import filtrer
from .ordres import OrdreInvalide

ACTIONS_MEME_ARRETEE = ("etat", "reprendre-file")


class Battement:
    """Pousse au plus tous les ``intervalle`` secondes un compte rendu « en cours »."""

    def __init__(self, ctx, depot, compte, spool, intervalle):
        self.ctx, self.depot, self.compte, self.spool, self.intervalle = ctx, depot, compte, spool, intervalle
        self.dernier = ctx.monotone()
        self.actif = intervalle > 0

    def __call__(self):
        if not self.actif or self.ctx.monotone() - self.dernier < self.intervalle:
            return
        self.dernier = self.ctx.monotone()
        self.compte.statut = EN_COURS
        texte = self.compte.rendre()
        ecriture.ecrire_texte(self.spool, texte)
        self.depot.publier(self.compte.stem, texte, EN_COURS)


def _reprendre_file(ctx, compte, ordre):
    cible = ordre.champs["file"]
    arret = ctx.registre.arret(cible)
    if not arret:
        raise Refus("la file %s n'est pas arrêtée" % cible)
    compte.ligne("File rouverte", "- file : %s" % cible)
    compte.ligne("File rouverte", "- elle avait été arrêtée par l'ordre %s le %s : %s"
                 % (arret["ordre"], arret["date"], arret["raison"]))
    ctx.registre.rouvrir(cible)
    return REUSSI


def executer_action(ctx, compte, ordre):
    a = ordre.action
    c = ordre.champs
    if a == "etat":
        return action_etat.etat(ctx, compte, ordre)
    if a == "adopter":
        return application.adopter(ctx, compte, ordre)
    if a == "deployer-application":
        return application.deployer(ctx, compte, ordre.id, c["commit"], c["version"])
    if a == "deployer-suite":
        return suites.deployer(ctx, compte, ordre)
    if a == "revenir":
        if c["cible"] == "application":
            return application.revenir(ctx, compte, ordre)
        return suites.revenir(ctx, compte, ordre)
    if a == "reprendre-file":
        return _reprendre_file(ctx, compte, ordre)
    if a == ordres.ACTION_FICHIERS:
        return fichiers.jouer(ctx, compte, ordre)
    raise Refus("action inconnue : %s" % a)


def jouer_ordre(ctx, depot, stem, texte):
    reg = ctx.registre
    file = ctx.file
    spool_dir = reg.chemin("resultats-" + file)
    os.makedirs(spool_dir, mode=0o700, exist_ok=True)
    spool = os.path.join(spool_dir, stem + ".md")
    compte = Compte(stem, texte)
    reg.marquer(file, stem, EN_COURS, debut=compte.debut)
    ctx.log("ordre %s : début" % stem)
    ctx.battement = Battement(ctx, depot, compte, spool, ctx.cfg.intervalle_en_cours_s)
    try:
        ordre = ordres.charger(texte, stem, ctx.cfg)
        arret = reg.arret(file)
        if arret and ordre.action not in ACTIONS_MEME_ARRETEE:
            raise Refus("file arrêtée depuis l'ordre %s : %s" % (arret["ordre"], arret["raison"]))
        compte.ligne("Action", "- %s demandée par %s" % (ordre.action, ordre.demande_par))
        statut = executer_action(ctx, compte, ordre)
    except (OrdreInvalide, Refus) as e:
        statut = REFUSE
        compte.ligne("Raison du refus", "- %s" % e)
        compte.decider("l'ordre est refusé, rien n'a bougé hors ce qui est dit ci-dessus ; corriger puis envoyer un nouvel ordre")
    except Exception as e:  # noqa: BLE001 - un bogue ne doit jamais laisser une file jouer la suite à l'aveugle
        ctx.log("erreur interne : %s" % traceback.format_exc().replace("\n", " | "))
        compte.ligne("Erreur interne", "- %s : %s" % (type(e).__name__, filtrer(str(e))))
        if file == ordres.FILE_DEPLOIEMENT:
            statut = ECHEC_ARRET
            ctx.registre.arreter(file, stem, "erreur interne du déployeur (%s)" % type(e).__name__, compterendu.horodatage())
            compte.ligne("File arrêtée", "- la file %s est arrêtée après une erreur interne" % file)
            compte.decider("erreur interne : vérifier l'état réel (ordre `etat`) avant de rouvrir la file avec `reprendre-file`")
        else:
            statut = REFUSE
    finally:
        ctx.battement = None
    compte.terminer(statut)
    texte_final = compte.rendre()
    ecriture.ecrire_texte(spool, texte_final)
    reg.marquer(file, stem, statut, fin=compte.fin)
    ctx.log("ordre %s : %s" % (stem, statut))
    depot.publier(stem, texte_final, statut)


def _interrompre(ctx, depot, stem):
    reg = ctx.registre
    texte = depot.texte_ordre(stem)
    compte = Compte(stem, texte or "(ordre introuvable dans la copie locale)")
    compte.debut = reg.journal(ctx.file).get(stem, {}).get("debut", compte.debut)
    compte.ligne("Interruption", "- l'ordre était marqué « en cours » au journal : le passage précédent a été coupé "
                 "(redémarrage, panne). Il n'est jamais rejoué.")
    compte.ligne("Interruption", "- l'état réel de la machine est inconnu : jouer un ordre `etat` pour le constater")
    compte.decider("constater l'état réel (ordre `etat`) ; si l'ordre voulait déployer, décider s'il faut en envoyer un nouveau")
    compte.terminer(INTERROMPU)
    texte_final = compte.rendre()
    spool = os.path.join(reg.chemin("resultats-" + ctx.file))
    os.makedirs(spool, mode=0o700, exist_ok=True)
    ecriture.ecrire_texte(os.path.join(spool, stem + ".md"), texte_final)
    reg.marquer(ctx.file, stem, INTERROMPU, fin=compte.fin)
    ctx.log("ordre %s : interrompu" % stem)
    depot.publier(stem, texte_final, INTERROMPU)


def _republier_manquants(ctx, depot):
    """Un compte rendu écrit sur la machine mais absent de la copie du dépôt est poussé de nouveau."""
    spool = ctx.registre.chemin("resultats-" + ctx.file)
    if not os.path.isdir(spool):
        return
    for nom in sorted(os.listdir(spool)):
        stem = nom[:-3]
        if nom.endswith(".md") and not depot.resultat_present(stem) \
                and ctx.registre.journal(ctx.file).get(stem, {}).get("statut") not in (None, EN_COURS):
            with open(os.path.join(spool, nom), "rb") as f:
                depot.publier(stem, f.read().decode("utf-8"), "republié")


def passage(ctx):
    reg = ctx.registre
    depot = DepotOrdres(ctx)
    try:
        depot.synchroniser()
    except Exception as e:  # noqa: BLE001
        ctx.log("dépôt d'ordres inaccessible : %s" % filtrer(str(e)))
        return 1
    _republier_manquants(ctx, depot)
    # 2. un ordre « en cours » au journal : interrompu, jamais rejoué
    for stem, entree in sorted(reg.journal(ctx.file).items()):
        if entree.get("statut") == EN_COURS:
            _interrompre(ctx, depot, stem)
    # 3. les ordres de la file pas encore au journal, par ordre d'id
    joues = 0
    for stem, chemin in depot.ordres():
        if stem in reg.journal(ctx.file):
            continue
        texte = depot.lire(chemin)
        if ordres.file_de(texte) != ctx.file:
            continue
        jouer_ordre(ctx, depot, stem, texte)
        joues += 1
    ctx.log("passage terminé : %d ordre(s) joué(s)" % joues)
    return 0


def executer(cfg, file, sortie=None, dormir=None, monotone=None):
    """Point d'entrée d'un passage (appelé par ``__main__``) ; retourne le code de sortie."""
    registre = reg_mod.Registre(cfg.repertoire_etat)
    registre.preparer()
    kw = {}
    if dormir is not None:
        kw["dormir"] = dormir
    if monotone is not None:
        kw["monotone"] = monotone
    ctx = Contexte(cfg, registre, file, sortie=sortie, **kw)
    with registre.verrou(file) as v:
        if not v.pris:
            ctx.log("verrou pris : un autre passage de la file est en cours, sortie sans rien faire")
            return 0
        return passage(ctx)
