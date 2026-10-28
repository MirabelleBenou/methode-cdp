"""Le dépôt d'ordres : une copie locale par file (``ordres-<file>/``), tenue à jour par avance rapide.

Le CdP écrit ``ordres/<id>.json`` ; le déployeur n'écrit que ``resultats/<id>.md``.
"""

import os

from . import commandes, ecriture
from .ordres import RE_STEM


class DepotOrdres:
    def __init__(self, ctx):
        self.ctx = ctx
        self.rep = ctx.registre.chemin("ordres-" + ctx.file)
        self.depot = ctx.cfg.depot_ordres
        self.git = ctx.cfg.git

    # -- synchronisation -------------------------------------------------------------------------
    def synchroniser(self):
        """Clone si besoin, valide ce qui traîne, récupère, avance (rebase) et pousse ce qui est en retard."""
        ctx = self.ctx
        acces = ctx.acces_ordres()
        if not os.path.isdir(os.path.join(self.rep, ".git")):
            commandes.git_cloner_ordres(acces, self.depot.url, self.rep, self.depot.branche)
            ctx.log("dépôt d'ordres cloné")
            return
        self._valider_en_attente()
        commandes.git_recuperer_ordres(acces, self.rep, self.depot.branche)
        try:
            commandes.git_rebaser(acces, self.rep, self.depot.branche, self.git.identite_nom, self.git.identite_courriel)
        except commandes.ErreurCommande:
            commandes.git_rebaser_abandonner(self.rep)
            raise
        if commandes.git_en_avance(self.rep, self.depot.branche) > 0:
            try:
                commandes.git_pousser(acces, self.rep, self.depot.branche)
                ctx.log("comptes rendus en attente poussés")
            except commandes.ErreurCommande as e:
                ctx.log("push différé : %s" % e)

    def _valider_en_attente(self):
        if commandes.git_modifications(self.rep).strip():
            commandes.git_ajouter(self.rep, "resultats")
            if not commandes.git_index_vide(self.rep):
                commandes.git_valider(self.rep, "Comptes rendus en attente", self.git.identite_nom,
                                      self.git.identite_courriel)

    # -- lecture des ordres ----------------------------------------------------------------------
    def ordres(self):
        """[(stem, chemin)] des fichiers ``ordres/*.json`` dont le nom est sûr, par ordre d'id."""
        dossier = os.path.join(self.rep, "ordres")
        try:
            noms = sorted(os.listdir(dossier))
        except FileNotFoundError:
            return []
        res = []
        for nom in noms:
            if not nom.endswith(".json"):
                continue
            stem = nom[:-5]
            chemin = os.path.join(dossier, nom)
            if RE_STEM.match(stem) and os.path.isfile(chemin) and not os.path.islink(chemin):
                res.append((stem, chemin))
        return res

    def lire(self, chemin):
        with open(chemin, "rb") as f:
            return f.read(1 << 20).decode("utf-8", "replace")

    def texte_ordre(self, stem):
        chemin = os.path.join(self.rep, "ordres", stem + ".json")
        return self.lire(chemin) if os.path.isfile(chemin) else ""

    def resultat_present(self, stem):
        return os.path.isfile(os.path.join(self.rep, "resultats", stem + ".md"))

    # -- publication -----------------------------------------------------------------------------
    def publier(self, stem, texte, statut):
        """Écrit ``resultats/<stem>.md``, valide, puis ``pull --rebase`` et ``push`` (trois essais).

        Un échec de push n'empêche pas la suite : il est retenté au passage suivant. Retourne True si poussé.
        """
        ctx = self.ctx
        acces = ctx.acces_ordres()
        dossier = os.path.join(self.rep, "resultats")
        os.makedirs(dossier, exist_ok=True)
        ecriture.ecrire_texte(os.path.join(dossier, stem + ".md"), texte)
        try:
            commandes.git_ajouter(self.rep, "resultats/%s.md" % stem)
            if not commandes.git_index_vide(self.rep):
                commandes.git_valider(self.rep, "Compte rendu %s : %s" % (stem, statut), self.git.identite_nom,
                                      self.git.identite_courriel)
        except commandes.ErreurCommande as e:
            ctx.log("commit du compte rendu impossible : %s" % e)
            return False
        for essai in range(3):
            try:
                commandes.git_rebaser(acces, self.rep, self.depot.branche, self.git.identite_nom,
                                      self.git.identite_courriel)
                commandes.git_pousser(acces, self.rep, self.depot.branche)
                ctx.log("compte rendu %s poussé" % stem)
                return True
            except commandes.ErreurCommande as e:
                commandes.git_rebaser_abandonner(self.rep)
                ctx.log("push du compte rendu %s : essai %d en échec : %s" % (stem, essai + 1, e))
                if essai < 2:
                    ctx.dormir(1)
        return False
