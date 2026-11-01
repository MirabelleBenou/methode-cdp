"""Tests de arbitre.py : un passage de l'arbitre sur un dépôt git temporaire, et le modèle de workflow.

Chaque test bâtit un dépôt git (git init, commits datés par GIT_COMMITTER_DATE) avec des vivants minimaux, y copie
les scripts (arbitre.py, le vérificateur, l'archiveur, le générateur) et lance arbitre.py avec « --date », pour que
les heures se comptent sans dépendre de l'horloge.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from .outils_tests import (ARCHIVER, GENERER, MODELES, SANS_PYYAML, VERIFIER, CasTemporaire, bloc,
                           charger, lecture_pyyaml, pyyaml, registre, sans_position, yaml)

ARBITRE = MODELES / "arbitre.py"
WORKFLOW = MODELES / "depot-vivants" / "arbitre.yml"

PASSAGE = "2026-03-15 06:43"        # l'heure de Paris du passage
BASE = "2026-03-01T10:00:00+0100"   # le commit de base
ENTETE_JOURNAL = "# Journal de l'arbitre\n\n"

TABLE = """# Domaines
- domaine: alpha
  cdp: Opus-CdP-Alpha
  checkpoint: Alpha/CHECKPOINT_ALPHA.md
  file: "## La file"
  modules: module-a
  prefixes: alpha-

- domaine: beta
  cdp: Opus-CdP-Beta
  checkpoint: Beta/CHECKPOINT_BETA.md
  file: "## La file"
  modules: module-b

- domaine: coordination
  cdp: Opus-Coordination
  checkpoint: Methode/CHECKPOINT_METHODE.md
  file: "## La file"
  modules: methode
"""

CHECKPOINTS = {
    "alpha": "Alpha/CHECKPOINT_ALPHA.md",
    "beta": "Beta/CHECKPOINT_BETA.md",
    "coordination": "Methode/CHECKPOINT_METHODE.md",
}
LIBRE = "Session en activité : aucune — libre depuis le 1er mars"


def checkpoint(*cites: str, temoin: str = LIBRE, remplissage: int = 0) -> str:
    """Un checkpoint : le témoin, puis une section « La file » qui cite les id donnés ; « remplissage » octets de plus."""
    file = "".join(f"- `{i}` à faire\n" for i in cites)
    texte = f"# Checkpoint\n\n{temoin}\n\n## La file\n{file}## Historique\nRien.\n"
    return texte + ("x" * remplissage + "\n" if remplissage else "")


def entrees(texte: str) -> list[dict]:
    """Les entrées d'un chantiers.yaml, lues comme les scripts les lisent."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "chantiers.yaml"
        chemin.write_bytes(texte.encode("utf-8"))
        return sans_position(charger(VERIFIER, "verifier_vivants_essai").lire_chantiers(chemin))


class CasArbitre(CasTemporaire):
    """Un dépôt git de vivants conformes ; chaque test en change une pièce, puis lance l'arbitre."""

    def setUp(self):
        super().setUp()
        self.depot = self.sous_dossier("depot")
        self.git("init", "-q", "-b", "main")
        for script in (ARBITRE, VERIFIER, ARCHIVER, GENERER):
            self.ecrire(f"depot/Methode/{script.name}", script.read_text(encoding="utf-8"))
        self.ecrire("depot/Methode/domaines.yaml", TABLE)
        self.ecrire("depot/Methode/ARBITRE_JOURNAL.md", ENTETE_JOURNAL)
        self.ecrire("depot/Methode/METHODE.md", "# Méthode\n")
        self.ecrire("depot/Dossier/registre.md", registre(1, 2, 3))
        os.makedirs(self.depot / "Dossier" / "Archives")
        self.ecrire("depot/Dossier/Archives/.gardien", "")
        self.chantiers_conformes()
        for domaine, chemin in CHECKPOINTS.items():
            self.ecrire(f"depot/{chemin}", checkpoint(*self.cites.get(domaine, ())))
        self.valider()

    cites = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def chantiers_conformes(self):
        self.ecrire_chantiers(bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
                              bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))

    # ── le dépôt ──

    def git(self, *arguments, quand: str | None = None):
        environnement = {**os.environ, "GIT_AUTHOR_NAME": "Essai", "GIT_AUTHOR_EMAIL": "essai@exemple.org",
                         "GIT_COMMITTER_NAME": "Essai", "GIT_COMMITTER_EMAIL": "essai@exemple.org"}
        if quand:
            environnement.update(GIT_COMMITTER_DATE=quand, GIT_AUTHOR_DATE=quand)
        processus = subprocess.run(["git", *arguments], cwd=self.depot, env=environnement, capture_output=True,
                                   text=True, encoding="utf-8")
        self.assertEqual(processus.returncode, 0, processus.stdout + processus.stderr)
        return processus.stdout

    def valider(self, message: str = "base", quand: str = BASE, tableau: bool = True):
        """Régénère le tableau (sauf « tableau=False »), puis un commit daté."""
        if tableau:
            sortie = self.lancer(GENERER, "Dossier/chantiers.yaml", "Dossier/chantiers.html", cwd=self.depot)
            self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message, quand=quand)

    def ecrire_chantiers(self, *blocs: str, entete: str = "# Chantiers — Essai") -> str:
        texte = yaml(*blocs, entete=entete)
        self.ecrire("depot/Dossier/chantiers.yaml", texte)
        return texte

    def lire(self, chemin: str) -> str:
        return (self.depot / chemin).read_bytes().decode("utf-8")

    def chantiers(self) -> list[dict]:
        return entrees(self.lire("Dossier/chantiers.yaml"))

    def par_id(self) -> dict:
        return {c["id"]: c for c in self.chantiers()}

    def arbitres(self) -> list[str]:
        return [c["id"] for c in self.chantiers() if c["id"].startswith("arbitre-")]

    def lignes_de_journal(self) -> list[str]:
        return [ligne for ligne in self.lire("Methode/ARBITRE_JOURNAL.md").split("\n") if ligne.startswith("- ")]

    def modifies(self) -> list[str]:
        return sorted(ligne[3:] for ligne in self.git("status", "--short").split("\n") if ligne)

    # ── l'arbitre ──

    def options(self, methode: bool = True, fiche: bool = False) -> list[str]:
        options = ["--chantiers", "Dossier/chantiers.yaml", "--registre", "Dossier/registre.md",
                   "--archives", "Dossier/Archives", "--domaines", "Methode/domaines.yaml",
                   "--journal-arbitre", "Methode/ARBITRE_JOURNAL.md",
                   "--tableau", "Dossier/chantiers.html", "--generateur", "Methode/generer_tableau.py"]
        if methode:
            options += ["--methode", "Methode/METHODE.md"]
        if fiche:
            options += ["--fiche", "Alpha/CHECKPOINT_ALPHA.md"]
        return options

    def arbitrer(self, *supplement, date: str | None = PASSAGE, options: list | None = None):
        arguments = self.options() if options is None else options
        if date:
            arguments = [*arguments, "--date", date]
        return self.lancer(self.depot / "Methode" / "arbitre.py", *arguments, *supplement, cwd=self.depot)

    def verifications(self):
        return ["--chantiers", "Dossier/chantiers.yaml", "--registre", "Dossier/registre.md",
                "--archives", "Dossier/Archives", "--domaines", "Methode/domaines.yaml",
                "--tableau", "Dossier/chantiers.html", "--generateur", "Methode/generer_tableau.py"]

    def commit_du_passage(self, sortie) -> str:
        m = re.search(r"^Commit : (.*)$", sortie.stdout, re.M)
        self.assertTrue(m, sortie.stdout)
        return m.group(1)


class TestConformes(CasArbitre):
    def test_des_vivants_conformes_rendent_0_et_n_ecrivent_que_le_journal(self):
        avant = {c: self.lire(c) for c in ("Dossier/chantiers.yaml", "Dossier/chantiers.html", "Dossier/chantiers.json")}
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.modifies(), ["Methode/ARBITRE_JOURNAL.md"])
        self.assertEqual({c: self.lire(c) for c in avant}, avant, "chantiers et tableau ne sont pas touchés")
        self.assertEqual(len(self.lignes_de_journal()), 1)
        self.assertRegex(self.lignes_de_journal()[0],
                         r"^- 2026-03-15 06:43 · 0 écart · 0 constat nouveau · témoins frais · "
                         r"archivage : 0 daté\(s\), 0 archivé\(s\) · checkpoints : à jour · socle : \d+ Ko$")
        self.assertTrue(self.lire("Methode/ARBITRE_JOURNAL.md").startswith(ENTETE_JOURNAL), "rien n'est réécrit")
        self.assertIn("Vivants conformes au 2026-03-15", sortie.stdout)
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : vivants conformes")

    def test_la_ligne_de_journal_s_ajoute_en_fin_sans_reecrire_les_precedentes(self):
        self.arbitrer(date="2026-03-15 06:43")
        premiere = self.lignes_de_journal()[0]
        self.arbitrer(date="2026-03-16 06:43")
        lignes = self.lignes_de_journal()
        self.assertEqual(len(lignes), 2)
        self.assertEqual(lignes[0], premiere)
        self.assertTrue(lignes[1].startswith("- 2026-03-16 06:43 · 0 écart"))

    def test_le_journal_sans_fin_de_ligne_recoit_sa_ligne_sur_une_ligne_neuve(self):
        self.ecrire("depot/Methode/ARBITRE_JOURNAL.md", "# Journal\n- 2026-03-14 06:43 · 0 écart")
        self.valider("journal sans fin de ligne")
        self.arbitrer()
        lignes = self.lire("Methode/ARBITRE_JOURNAL.md").split("\n")
        self.assertEqual(lignes[1], "- 2026-03-14 06:43 · 0 écart")
        self.assertTrue(lignes[2].startswith("- 2026-03-15 06:43"))

    def test_la_date_du_jour_par_defaut_est_l_heure_de_paris(self):
        sortie = self.arbitrer(date=None)
        self.assertEqual(sortie.code, 0, sortie.stderr)
        self.assertRegex(self.lignes_de_journal()[0], r"^- \d{4}-\d{2}-\d{2} \d{2}:\d{2} · 0 écart")

    def test_aucun_bytecode_n_est_ecrit_dans_le_depot(self):
        self.arbitrer()
        self.assertEqual([p for p in self.depot.rglob("__pycache__")], [])


class TestEcartNouveau(CasArbitre):
    cites = {"alpha": ("alpha-1", "alpha-2"), "beta": ("beta-1",)}

    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Deuxième", statut="en-vol", module="module-a"),  # en vol sans cdp : contrôle 5
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))

    def test_un_ecart_nouveau_fait_un_chantier_de_la_bonne_forme_et_rend_1(self):
        avant = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        ligne = next(i for i, texte in enumerate(avant.split("\n"), start=1) if texte == "- id: alpha-2")
        attendu = (
            "\n- id: arbitre-c5-alpha-2\n"
            f"  titre: \"Contrôle 5 : alpha-2 (ligne {ligne}) : cdp absent ou vide\"\n"
            "  module: module-a\n"
            "  categorie: doc\n"
            "  statut: a-cadrer\n"
            "  pour: Opus-CdP-Alpha\n"
            "  priorite: moyen\n"
            "  complexite: faible\n"
            "  cout: aucun ; une correction dans les vivants\n"
            "  mesure: \"Signalé par l'arbitre le 15 mars 2026 (contrôle 5). "
            f"alpha-2 (ligne {ligne}) : cdp absent ou vide. Renseigner le cdp: du chantier en vol.\"\n"
            "  refs: Methode/ARBITRE.md\n")
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), avant + attendu)
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : 1 constat(s)")
        self.assertIn("Constats nouveaux (1) :\n  - arbitre-c5-alpha-2 · pour Opus-CdP-Alpha", sortie.stdout)
        self.assertRegex(self.lignes_de_journal()[0], r"^- 2026-03-15 06:43 · 1 écart · 1 constat nouveau · ")

    def test_le_tableau_est_regenere_puis_le_controle_6_est_ok(self):
        self.arbitrer()
        # la page est fixe : seules les données changent
        self.assertEqual(self.modifies(), ["Dossier/chantiers.json", "Dossier/chantiers.yaml", "Methode/ARBITRE_JOURNAL.md"])
        self.assertIn("arbitre-c5-alpha-2", self.lire("Dossier/chantiers.json"))
        controle = self.lancer(self.depot / "Methode" / "verifier_vivants.py", *self.verifications(), cwd=self.depot)
        self.assertEqual(controle.verdict(6), "OK", controle.stdout)

    def test_le_meme_ecart_au_passage_suivant_ne_fait_pas_de_doublon(self):
        self.arbitrer()
        apres_le_premier = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer(date="2026-03-16 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres_le_premier)
        self.assertEqual(self.arbitres(), ["arbitre-c5-alpha-2"])
        self.assertIn("Déjà signalés et toujours là (1) :\n  - arbitre-c5-alpha-2 · pour Opus-CdP-Alpha", sortie.stdout)
        self.assertRegex(self.lignes_de_journal()[1], r"^- 2026-03-16 06:43 · 1 écart · 0 constat nouveau · ")
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-16 : 0 constat(s)")

    def test_un_chantier_deja_en_recette_couvre_encore_le_cas(self):
        self.arbitrer()
        texte = self.lire("Dossier/chantiers.yaml").replace(
            "  statut: a-cadrer\n  pour: Opus-CdP-Alpha", "  statut: recette\n  pour: Opus-CdP-Alpha")
        self.ecrire("depot/Dossier/chantiers.yaml", texte)
        self.valider("le CdP passe le constat en recette")
        sortie = self.arbitrer(date="2026-03-16 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertEqual(self.arbitres(), ["arbitre-c5-alpha-2"])

    def test_un_id_archive_ne_se_reutilise_pas_on_ajoute_la_date(self):
        self.arbitrer()
        entree = [b for b in self.lire("Dossier/chantiers.yaml").split("\n\n") if b.startswith("- id: arbitre-c5-alpha-2")][0]
        self.ecrire("depot/Dossier/chantiers.yaml", self.lire("Dossier/chantiers.yaml").replace("\n\n" + entree, "\n"))
        self.ecrire("depot/Dossier/Archives/CHANTIERS_2026-03.yaml",
                    "# Chantiers archivés — mars 2026\n\n" + entree.replace("a-cadrer", "recette"))
        self.valider("le constat est archivé, le cas revient")
        sortie = self.arbitrer(date="2026-03-20 06:43")
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c5-alpha-2-20260320"])
        controle = self.lancer(self.depot / "Methode" / "verifier_vivants.py", *self.verifications(), cwd=self.depot)
        self.assertEqual(controle.verdict(3), "OK", controle.stdout)

    @SANS_PYYAML
    def test_les_chantiers_ecrits_se_lisent_pareil_par_un_parseur_yaml_standard(self):
        self.arbitrer()
        texte = self.lire("Dossier/chantiers.yaml")
        self.assertEqual(lecture_pyyaml(texte), self.chantiers())


class TestDestinataires(CasArbitre):
    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"),
            bloc("beta-2", titre="En vol", statut="en-vol", module="module-b", cdp="Opus-CdP-Autre"),
            bloc("orphelin-1", titre="Sans domaine", statut="en-vol", module="module-z", version="v1"),
            bloc("orphelin-2", titre="Sans domaine non plus", statut="a-venir", module="module-z", version="v1"))

    cites = {"alpha": ("alpha-1",), "beta": ("beta-1", "beta-2")}

    def test_un_chantier_en_vol_va_au_cdp_qu_il_porte_un_module_sans_cdp_au_coordinateur(self):
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        arbitres = self.par_id()
        # orphelin-1 : en vol sans cdp, ni domaine ; orphelin-2 porte la même version
        self.assertEqual(arbitres["arbitre-c5-orphelin-1"]["pour"], "Opus-Coordination")
        self.assertEqual(arbitres["arbitre-c5-orphelin-1"]["module"], "module-z")
        self.assertEqual(arbitres["arbitre-c4-orphelin-1"]["pour"], "Opus-Coordination")

    def test_le_registre_le_tableau_et_le_journal_vont_au_coordinateur(self):
        self.ecrire("depot/Dossier/registre.md", registre(1, 3))
        self.ecrire("depot/Dossier/chantiers.html", "<html>périmé</html>")
        self.valider("registre troué, tableau périmé", tableau=False)
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout)
        arbitres = self.par_id()
        for i in ("arbitre-c1-R2", "arbitre-c6-tableau"):
            self.assertEqual(arbitres[i]["pour"], "Opus-Coordination", i)
            self.assertEqual(arbitres[i]["module"], "methode", i)
        self.assertIn("R2 manquant", arbitres["arbitre-c1-R2"]["mesure"])
        self.assertIn("la page du tableau diffère", arbitres["arbitre-c6-tableau"]["mesure"])
        self.assertNotIn("arbitre-c6-tableau-2", arbitres)

    def test_deux_lots_en_vol_sur_une_meme_ressource_un_chantier_chacun_vers_son_cdp(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="en-vol", module="module-a", cdp="Opus-CdP-Alpha", ressource="machine"),
            bloc("beta-1", titre="Autre", statut="en-vol", module="module-b", cdp="Opus-CdP-Beta", ressource="machine"))
        self.valider("deux lots sur la machine")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout)
        arbitres = self.par_id()
        self.assertEqual(arbitres["arbitre-c8-alpha-1"]["pour"], "Opus-CdP-Alpha")
        self.assertEqual(arbitres["arbitre-c8-beta-1"]["pour"], "Opus-CdP-Beta")
        self.assertEqual(arbitres["arbitre-c8-beta-1"]["module"], "module-b")
        self.assertIn("ressource machine : 2 lots en vol (alpha-1, beta-1)", arbitres["arbitre-c8-beta-1"]["mesure"])

    def test_un_lot_en_vol_qui_porte_un_cdp_etranger_a_la_table_va_a_ce_cdp(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="en-vol", module="module-a", cdp="Opus-CdP-Autre", livrable="depot"),
            bloc("alpha-2", titre="Second", statut="en-vol", module="module-a", cdp="Opus-CdP-Alpha", livrable="depot"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))
        self.valider("deux lots sur un livrable")
        self.assertEqual(self.arbitrer().code, 1)
        arbitres = self.par_id()
        self.assertEqual(arbitres["arbitre-c8-alpha-1"]["pour"], "Opus-CdP-Autre")
        self.assertEqual(arbitres["arbitre-c8-alpha-2"]["pour"], "Opus-CdP-Alpha")

    def test_un_lot_en_vol_sous_la_plus_haute_version_de_son_livrable_va_a_son_cdp(self):
        # contrôle 4 (b) : la clé et le chantier en cause sont l'id en tête de la ligne
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a", livrable="depot", version="v1.2"),
            bloc("alpha-2", titre="Second", statut="en-vol", module="module-a", cdp="Opus-CdP-Alpha", livrable="depot",
                 version="v1.1"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))
        self.valider("un lot en vol sous la plus haute version")
        self.assertEqual(self.arbitrer().code, 1)
        arbitres = self.par_id()
        self.assertNotIn("arbitre-c4-alpha-1", arbitres)
        self.assertEqual(arbitres["arbitre-c4-alpha-2"]["pour"], "Opus-CdP-Alpha")
        self.assertEqual(arbitres["arbitre-c4-alpha-2"]["module"], "module-a")
        self.assertIn("alpha-2 : v1.1 n'est pas au-dessus de v1.2 (alpha-1)", arbitres["arbitre-c4-alpha-2"]["mesure"])
        self.assertIn("un lot en vol passe au-dessus de la plus haute version de son livrable",
                      arbitres["arbitre-c4-alpha-2"]["mesure"])

    def test_les_deux_formes_du_controle_4_donnent_l_id_en_cause(self):
        arbitre = charger(ARBITRE, "arbitre_sous_test")

        class Ctx:
            par_id = {"agent-serveur-essai": {"id": "agent-serveur-essai"}, "alpha-1": {"id": "alpha-1"}}

        cas = arbitre.cas_du_controle(
            4, "essai-recul : agent-v0.1.0 n'est pas au-dessus de agent-v0.1.1 (agent-serveur-essai)", Ctx)
        self.assertEqual(cas, [("essai-recul", None)])
        cas = arbitre.cas_du_controle(
            4, "agent-serveur-essai : agent-v0.1.0 n'est pas au-dessus de agent-v0.1.1 (alpha-1)", Ctx)
        self.assertEqual(cas, [("agent-serveur-essai", {"id": "agent-serveur-essai"})])
        cas = arbitre.cas_du_controle(4, "version v1 portée par alpha-1 et beta-2", Ctx)
        self.assertEqual(cas, [("alpha-1", {"id": "alpha-1"})])

    def test_l_ecart_b_du_controle_4_se_lit_meme_si_la_version_contient_une_espace(self):
        arbitre = charger(ARBITRE, "arbitre_sous_test")

        class Ctx:
            par_id = {"co-x": {"id": "co-x"}, "co-y": {"id": "co-y"}}

        cas = arbitre.cas_du_controle(4, "co-x : v1.2 (R205) n'est pas au-dessus de v1.3 (co-y)", Ctx)
        self.assertEqual(cas, [("co-x", {"id": "co-x"})])

    def test_le_coordinateur_se_lit_dans_la_table_des_domaines(self):
        table = TABLE.replace("Opus-Coordination", "Opus-Coordination-Autre")
        self.ecrire("depot/Methode/domaines.yaml", table)
        self.valider("un autre nom de coordinateur")
        self.arbitrer()
        self.assertEqual(self.par_id()["arbitre-c5-orphelin-1"]["pour"], "Opus-Coordination-Autre")

    def test_le_mot_coordination_peut_etre_n_importe_ou_dans_le_cdp_du_coordinateur(self):
        table = TABLE.replace("Opus-Coordination", "Pilotage-Coordination-Opus")
        self.ecrire("depot/Methode/domaines.yaml", table)
        self.valider("un coordinateur au nom composé")
        self.arbitrer()
        self.assertEqual(self.par_id()["arbitre-c5-orphelin-1"]["pour"], "Pilotage-Coordination-Opus")

    def test_sans_entree_coordination_le_script_sort_en_code_2_et_n_ecrit_que_le_journal(self):
        table = TABLE.replace("Opus-Coordination", "Opus-Autre")
        self.ecrire("depot/Methode/domaines.yaml", table)
        self.valider("plus de coordinateur")
        avant = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2)
        self.assertIn("aucune entrée Coordination", sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), avant)
        self.assertEqual(self.modifies(), ["Methode/ARBITRE_JOURNAL.md"])
        self.assertRegex(self.lignes_de_journal()[0], r"^- 2026-03-15 06:43 · contrôle impossible : Methode/domaines\.yaml$")


class TestControle9Groupe(CasArbitre):
    cites = {"alpha": (), "beta": ("beta-1",)}

    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Deuxième", statut="dette", module="module-a"),
            bloc("alpha-3", titre="Troisième", statut="a-cadrer", module="module-a"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"),
            bloc("beta-2", titre="Autre encore", statut="a-venir", module="module-b"))

    def test_le_controle_9_fait_un_chantier_par_domaine_et_non_un_par_ligne(self):
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c9-checkpoint-alpha-20260315", "arbitre-c9-checkpoint-beta-20260315"])
        alpha = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]
        self.assertEqual((alpha["pour"], alpha["module"]), ("Opus-CdP-Alpha", "methode"))
        self.assertEqual(alpha["titre"], "Le checkpoint de alpha est en retard sur ses chantiers")
        self.assertEqual(alpha["mesure"], (
            "Signalé par l'arbitre le 15 mars 2026 (contrôle 9). "
            "alpha : alpha-1 (a-venir) n'est pas cité au checkpoint ; alpha : alpha-2 (dette) n'est pas cité au "
            "checkpoint ; alpha : alpha-3 (a-cadrer) n'est pas cité au checkpoint. "
            "Citer chaque chantier ouvert de ton domaine par son id dans ton checkpoint, retirer de ta file les "
            "chantiers clos (méthode §6)."))
        beta = self.par_id()["arbitre-c9-checkpoint-beta-20260315"]
        self.assertEqual(beta["pour"], "Opus-CdP-Beta")
        self.assertIn("beta : beta-2 (a-venir) n'est pas cité au checkpoint", beta["mesure"])
        self.assertRegex(self.lignes_de_journal()[0], r"· 1 écart · 2 constats nouveaux · témoins frais · .*"
                                                      r"· checkpoints : alpha, beta · socle")

    def test_un_chantier_du_domaine_encore_ouvert_empeche_un_nouveau_depot_meme_un_autre_jour(self):
        self.arbitrer()
        apres = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer(date="2026-03-17 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres)
        self.assertEqual(self.arbitres(), ["arbitre-c9-checkpoint-alpha-20260315", "arbitre-c9-checkpoint-beta-20260315"])

    def test_un_chantier_en_recette_ne_couvre_plus_le_domaine(self):
        self.arbitrer()
        texte = self.lire("Dossier/chantiers.yaml").replace(
            "  statut: a-cadrer\n  pour: Opus-CdP-Alpha", "  statut: recette\n  pour: Opus-CdP-Alpha")
        self.ecrire("depot/Dossier/chantiers.yaml", texte)
        self.valider("le CdP d'alpha passe son constat en recette")
        sortie = self.arbitrer(date="2026-03-17 06:43")
        self.assertEqual(sortie.code, 1, sortie.stdout)
        self.assertIn("arbitre-c9-checkpoint-alpha-20260317", self.arbitres())

    def test_un_nom_de_domaine_prefixe_d_un_autre_ne_se_confond_pas_avec_lui(self):
        table = TABLE + ("\n- domaine: beta-bis\n  cdp: Opus-CdP-Bis\n  checkpoint: Beta/CHECKPOINT_BIS.md\n"
                         "  file: \"## La file\"\n  modules: module-c\n")
        self.ecrire("depot/Methode/domaines.yaml", table)
        self.ecrire("depot/Beta/CHECKPOINT_BIS.md", checkpoint("bis-1"))
        self.ecrire_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                              bloc("beta-1", statut="a-venir", module="module-b"),
                              bloc("bis-1", statut="a-venir", module="module-c"),
                              bloc("arbitre-c9-checkpoint-beta-bis-20260301", titre="Ancien", statut="a-cadrer",
                                   module="methode", pour="Opus-CdP-Bis"))
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.ecrire("depot/Beta/CHECKPOINT_BETA.md", checkpoint())
        self.valider("un domaine beta-bis ouvert")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertIn("arbitre-c9-checkpoint-beta-20260315", self.arbitres())


class TestControle9Table(CasArbitre):
    def test_un_defaut_de_la_table_va_au_coordinateur_en_un_seul_chantier(self):
        os.remove(self.depot / "Beta" / "CHECKPOINT_BETA.md")
        os.remove(self.depot / "Alpha" / "CHECKPOINT_ALPHA.md")
        self.valider("deux checkpoints perdus")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c9-table-20260315"])
        table = self.par_id()["arbitre-c9-table-20260315"]
        self.assertEqual((table["pour"], table["module"]), ("Opus-Coordination", "methode"))
        self.assertIn("alpha : checkpoint introuvable Alpha/CHECKPOINT_ALPHA.md ; "
                      "beta : checkpoint introuvable Beta/CHECKPOINT_BETA.md", table["mesure"])

    def test_jamais_redepose_tant_qu_un_chantier_de_table_est_ouvert(self):
        os.remove(self.depot / "Beta" / "CHECKPOINT_BETA.md")
        self.valider("un checkpoint perdu")
        self.arbitrer()
        apres = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer(date="2026-03-18 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres)

    def test_une_section_de_file_vide_dans_la_table_est_un_ecart_du_domaine_pas_de_la_table(self):
        self.ecrire("depot/Methode/domaines.yaml", TABLE.replace('  file: "## La file"\n  modules: module-a',
                                                                 '  file:\n  modules: module-a'))
        self.valider("file non déclarée")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c9-checkpoint-alpha-20260315"])
        self.assertIn("alpha : aucune section de file déclarée", self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]["mesure"])


class TestControle10(CasArbitre):
    def poser_un_checkpoint_lourd(self):
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", remplissage=11000))
        self.valider("un checkpoint lourd")

    def test_un_checkpoint_de_plus_de_10_ko_fait_un_chantier_par_domaine(self):
        self.poser_un_checkpoint_lourd()
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c10-checkpoint-court-alpha-20260315"])
        c = self.par_id()["arbitre-c10-checkpoint-court-alpha-20260315"]
        self.assertEqual((c["pour"], c["module"]), ("Opus-CdP-Alpha", "methode"))
        self.assertEqual(c["titre"], "Le checkpoint de alpha dépasse 10 Ko")
        self.assertRegex(c["mesure"], r"^Signalé par l'arbitre le 15 mars 2026 \(contrôle 10\)\. alpha : "
                                      r"Alpha/CHECKPOINT_ALPHA\.md pèse \d+ octets, plafond 10240\. "
                                      r"Sortir l'historique vers `Alpha/Archives/`, cité en une ligne ; "
                                      r"le checkpoint tient en 10 Ko \(méthode §6\)\.$")
        self.assertRegex(self.lignes_de_journal()[0], r"· checkpoints : alpha · socle")

    def test_pas_de_doublon_au_passage_suivant(self):
        self.poser_un_checkpoint_lourd()
        self.arbitrer()
        apres = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer(date="2026-03-16 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres)

    def test_un_chantier_ouvert_pour_ce_cdp_qui_porte_checkpoint_court_suffit(self):
        self.poser_un_checkpoint_lourd()
        self.ecrire_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                              bloc("beta-1", statut="a-venir", module="module-b"),
                              bloc("alpha-checkpoint-court", titre="Fait à la main", statut="a-cadrer",
                                   module="module-a", pour="Opus-CdP-Alpha"))
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-checkpoint-court", remplissage=11000))
        self.valider("un constat posé à la main")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])


def long(id: str, octets: int = 1700, **cles) -> str:
    """Une entrée de chantier de « octets » octets (ses lignes, chacune suivie d'un saut de ligne), au-delà du plafond."""
    base = bloc(id, **cles, mesure="")
    vide = sum(len(ligne.encode("utf-8")) + 1 for ligne in base.split("\n"))
    return bloc(id, **cles, mesure="x" * (octets - vide))


def decision(numero: int, caracteres: int) -> str:
    """Une ligne « | **R<n>** | … | » de « caracteres » caractères."""
    debut, fin = f"| **R{numero}** | ", " |"
    return debut + "x" * (caracteres - len(debut) - len(fin)) + fin


class TestControle12(CasArbitre):
    """Les entrées trop longues : un chantier par domaine ; « hors domaine » et « registre » vont au coordinateur."""
    cites = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def poser(self, *blocs: str, decisions: tuple = ()):
        self.ecrire_chantiers(*blocs)
        self.ecrire("depot/Dossier/registre.md", registre(1, 2, 3) + "".join(f"{d}\n" for d in decisions))
        self.valider("des entrées longues")

    def chantiers_longs(self):
        return (long("alpha-1", 1700, statut="a-venir", module="module-a"),
                long("beta-1", 1600, statut="a-venir", module="module-b"))

    def avec_registre(self, depuis: str = "4"):
        return self.arbitrer("--registre-depuis", depuis)

    def test_un_chantier_trop_long_fait_un_chantier_par_domaine(self):
        self.poser(*self.chantiers_longs())
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-alpha-20260315",
                                           "arbitre-c12-entrees-courtes-beta-20260315"])
        alpha = self.par_id()["arbitre-c12-entrees-courtes-alpha-20260315"]
        self.assertEqual((alpha["pour"], alpha["module"], alpha["statut"]), ("Opus-CdP-Alpha", "methode", "a-cadrer"))
        self.assertEqual(alpha["titre"], "Des entrées de alpha dépassent leur plafond")
        self.assertEqual(alpha["mesure"], (
            "Signalé par l'arbitre le 15 mars 2026 (contrôle 12). "
            "alpha : chantier alpha-1 pèse 1700 octets, plafond 1536. "
            "Ramener chaque entrée sous son plafond (méthode §6) : l'état, la décision, le prochain geste ; "
            "le détail part au dossier du lot ou à une note du domaine, l'entrée n'en garde que le résumé et le chemin."))
        beta = self.par_id()["arbitre-c12-entrees-courtes-beta-20260315"]
        self.assertEqual((beta["pour"], beta["titre"]), ("Opus-CdP-Beta", "Des entrées de beta dépassent leur plafond"))
        self.assertIn("beta : chantier beta-1 pèse 1600 octets, plafond 1536", beta["mesure"])
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : 2 constat(s)")
        self.assertRegex(self.lignes_de_journal()[0], r"^- 2026-03-15 06:43 · 1 écart · 2 constats nouveaux · ")

    def test_plusieurs_lignes_d_un_domaine_font_un_seul_chantier_jointes_par_un_point_virgule(self):
        self.poser(long("alpha-1", 1700, statut="a-venir", module="module-a"),
                   long("alpha-2", 1800, statut="a-cadrer", module="module-a"),
                   bloc("beta-1", statut="a-venir", module="module-b"))
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-2"))
        self.valider("alpha-2 cité")
        self.arbitrer()
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-alpha-20260315"])
        self.assertIn("(contrôle 12). alpha : chantier alpha-1 pèse 1700 octets, plafond 1536 ; "
                      "alpha : chantier alpha-2 pèse 1800 octets, plafond 1536. Ramener",
                      self.par_id()["arbitre-c12-entrees-courtes-alpha-20260315"]["mesure"])

    def test_hors_domaine_et_registre_vont_au_domaine_du_coordinateur_dans_l_ordre_de_la_table(self):
        self.poser(long("orphelin-1", 1900, statut="dette", module="inconnu"), *self.chantiers_longs(),
                   decisions=(decision(4, 900), decision(5, 100), decision(6, 801)))
        sortie = self.avec_registre()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-alpha-20260315",
                                           "arbitre-c12-entrees-courtes-beta-20260315",
                                           "arbitre-c12-entrees-courtes-coordination-20260315"])
        c = self.par_id()["arbitre-c12-entrees-courtes-coordination-20260315"]
        self.assertEqual((c["pour"], c["module"], c["titre"]),
                         ("Opus-Coordination", "methode", "Des entrées de coordination dépassent leur plafond"))
        self.assertIn("(contrôle 12). hors domaine : chantier orphelin-1 pèse 1900 octets, plafond 1536 ; "
                      "registre : R4 compte 900 caractères, plafond 800 ; "
                      "registre : R6 compte 801 caractères, plafond 800. Ramener", c["mesure"])
        self.assertIn("Constats nouveaux (3) :", sortie.stdout)

    def test_le_domaine_du_coordinateur_groupe_aussi_ses_propres_lignes(self):
        self.poser(long("methode-1", 1700, statut="a-venir", module="methode"),
                   bloc("alpha-1", statut="a-venir", module="module-a"), bloc("beta-1", statut="a-venir", module="module-b"),
                   decisions=(decision(4, 900),))
        self.ecrire("depot/Methode/CHECKPOINT_METHODE.md", checkpoint("methode-1"))
        self.valider("methode-1 cité")
        self.avec_registre()
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-coordination-20260315"])
        self.assertIn("(contrôle 12). coordination : chantier methode-1 pèse 1700 octets, plafond 1536 ; "
                      "registre : R4 compte 900 caractères, plafond 800. Ramener",
                      self.par_id()["arbitre-c12-entrees-courtes-coordination-20260315"]["mesure"])

    def test_les_chantiers_du_controle_12_viennent_apres_ceux_des_controles_9_et_10(self):
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", remplissage=11000))
        self.poser(*self.chantiers_longs(), bloc("beta-2", statut="a-venir", module="module-b"))
        self.arbitrer()
        self.assertEqual(self.arbitres(), [
            "arbitre-c9-checkpoint-beta-20260315", "arbitre-c10-checkpoint-court-alpha-20260315",
            "arbitre-c12-entrees-courtes-alpha-20260315", "arbitre-c12-entrees-courtes-beta-20260315"])

    def test_sans_registre_depuis_le_registre_n_est_pas_mesure(self):
        self.poser(*[bloc("alpha-1", statut="a-venir", module="module-a"), bloc("beta-1", statut="a-venir", module="module-b")],
                   decisions=(decision(4, 5000),))
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])

    def test_registre_depuis_est_passee_telle_quelle_et_vide_elle_n_est_pas_passee(self):
        self.poser(*[bloc("alpha-1", statut="a-venir", module="module-a"), bloc("beta-1", statut="a-venir", module="module-b")],
                   decisions=(decision(4, 900), decision(5, 900)))
        self.avec_registre("5")
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-coordination-20260315"])
        mesure = self.par_id()["arbitre-c12-entrees-courtes-coordination-20260315"]["mesure"]
        self.assertIn("registre : R5 compte 900 caractères", mesure)
        self.assertNotIn("R4 compte", mesure)

    def test_une_valeur_de_registre_depuis_invalide_est_un_controle_impossible(self):
        self.poser(*self.chantiers_longs())
        sortie = self.avec_registre("abc")
        self.assertEqual(sortie.code, 2, sortie.stdout + sortie.stderr)
        self.assertIn("verifier_vivants.py a échoué (code 2)", sortie.stderr)
        self.assertEqual(self.arbitres(), [])
        self.assertRegex(self.lignes_de_journal()[0], r"contrôle impossible : verifier_vivants\.py$")

    def test_pas_de_doublon_au_passage_suivant_meme_un_autre_jour(self):
        self.poser(*self.chantiers_longs(), decisions=(decision(4, 900),))
        self.avec_registre()
        apres = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer("--registre-depuis", "4", date="2026-03-16 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres)
        self.assertEqual(len(self.arbitres()), 3)
        self.assertIn("Déjà signalés et toujours là (3) :", sortie.stdout)

    def test_les_chantiers_deposes_ne_sont_pas_mesures_eux_memes(self):
        self.poser(*self.chantiers_longs(), decisions=(decision(4, 900),))
        self.avec_registre()
        controle = self.lancer(self.depot / "Methode" / "verifier_vivants.py", *self.verifications(), "--registre-depuis", "4",
                               cwd=self.depot)
        self.assertEqual(controle.compte(12), "2 chantiers ouverts, 1 entrées du registre, 3 au-delà", controle.stdout)

    def test_un_chantier_ouvert_pour_ce_cdp_dont_l_id_porte_entrees_courtes_suffit(self):
        self.poser(*self.chantiers_longs(),
                   bloc("alpha-entrees-courtes", titre="Fait à la main", statut="a-cadrer", module="module-a",
                        pour="Opus-CdP-Alpha"))
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.valider("un constat posé à la main")
        sortie = self.arbitrer()
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-beta-20260315"])
        self.assertIn("Déjà signalés et toujours là (1) :\n  - alpha-entrees-courtes · pour Opus-CdP-Alpha", sortie.stdout)

    def test_un_chantier_en_recette_ou_pour_un_autre_cdp_ne_couvre_pas(self):
        self.poser(*self.chantiers_longs(),
                   bloc("alpha-entrees-courtes", statut="recette", module="module-a", pour="Opus-CdP-Alpha"),
                   bloc("gamma-entrees-courtes", statut="a-cadrer", module="module-b", pour="Opus-CdP-Gamma"))
        self.arbitrer()
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-alpha-20260315",
                                           "arbitre-c12-entrees-courtes-beta-20260315"])

    def test_un_id_archive_ne_se_reutilise_pas_on_ajoute_la_date(self):
        self.poser(*self.chantiers_longs())
        self.ecrire("depot/Dossier/Archives/CHANTIERS_2026-03.yaml", "# Chantiers archivés — mars 2026\n\n" + bloc(
            "arbitre-c12-entrees-courtes-alpha-20260315", statut="recette", module="methode", pour="Opus-CdP-Alpha"))
        self.valider("un constat de ce jour déjà archivé")
        self.arbitrer()
        self.assertEqual(self.arbitres(), ["arbitre-c12-entrees-courtes-alpha-20260315-20260315",
                                           "arbitre-c12-entrees-courtes-beta-20260315"])

    def test_les_autres_constats_sont_ceux_d_avant(self):
        self.poser(bloc("alpha-1", statut="en-vol", module="module-a"),  # en vol sans cdp : contrôle 5
                   long("beta-1", 1600, statut="a-venir", module="module-b"))
        self.arbitrer()
        self.assertEqual(self.arbitres(), ["arbitre-c5-alpha-1", "arbitre-c12-entrees-courtes-beta-20260315"])
        self.assertEqual(self.par_id()["arbitre-c5-alpha-1"]["titre"],
                         "Contrôle 5 : alpha-1 (ligne 3) : cdp absent ou vide")

    def test_la_docstring_decrit_le_controle_12_et_l_option(self):
        doc = charger(ARBITRE, "arbitre_doc").__doc__
        for attendu in ("--registre-depuis", "arbitre-c12-entrees-courtes-<domaine>-<AAAAMMJJ>", "entrees-courtes"):
            self.assertIn(attendu, doc)


class TestTemoins(CasArbitre):
    def poser_un_temoin(self, domaine: str, identifiant: str, depuis: str = "le 1er mars"):
        self.ecrire(f"depot/{CHECKPOINTS[domaine]}", checkpoint(*self.cites.get(domaine, ()),
                    temoin=f"**Session en activité : {identifiant}, depuis {depuis}**"))

    def test_un_temoin_silencieux_depuis_plus_de_24_h_va_au_journal_et_a_la_sortie_sans_chantier(self):
        self.poser_un_temoin("alpha", "AbCd1234")
        self.valider("Alpha : reprise\n\nClaude-Session: https://claude.ai/code/session_01XYZAbCd1234",
                     quand="2026-03-14T04:00:00+0100")
        avant = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), avant)
        self.assertEqual(self.arbitres(), [])
        self.assertIn("alpha (AbCd1234, dernier commit le 2026-03-14 04:00)", self.lignes_de_journal()[0])
        self.assertIn("Témoins · alpha (AbCd1234, dernier commit le 2026-03-14 04:00)", sortie.stdout)

    def test_un_temoin_qui_a_commite_depuis_moins_de_24_h_est_frais(self):
        self.poser_un_temoin("alpha", "AbCd1234")
        self.valider("Alpha : reprise AbCd1234", quand="2026-03-14T08:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertIn("· témoins frais ·", self.lignes_de_journal()[0])

    def test_le_temoin_le_plus_ancien_est_donne(self):
        self.poser_un_temoin("alpha", "AbCd1234")
        self.poser_un_temoin("beta", "ZyXw9876")
        self.valider("Alpha AbCd1234", quand="2026-03-13T10:00:00+0100")
        self.valider("Beta ZyXw9876", quand="2026-03-11T10:00:00+0100")
        self.arbitrer()
        self.assertIn("· beta (ZyXw9876, dernier commit le 2026-03-11 10:00) ·", self.lignes_de_journal()[0])

    def test_la_coordination_est_exclue_des_temoins(self):
        self.poser_un_temoin("coordination", "CoOr5678", depuis="le 1er mars")
        self.valider("Coordination CoOr5678", quand="2026-03-05T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertIn("· témoins frais ·", self.lignes_de_journal()[0])

    def test_sans_aucun_commit_du_temoin_le_dernier_commit_du_checkpoint_tient_lieu_de_pose(self):
        self.poser_un_temoin("alpha", "AbCd1234")
        self.valider("Alpha : un témoin sans trace de session", quand="2026-03-10T10:00:00+0100")
        self.arbitrer()
        self.assertIn("alpha (AbCd1234, aucun commit, checkpoint touché le 2026-03-10 10:00)",
                      self.lignes_de_journal()[0])

    def test_un_temoin_libre_ou_sans_objet_n_est_pas_controle(self):
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1", temoin="**Session en activité : sans objet — fiche.**"))
        self.valider("fiche", quand="2026-03-02T10:00:00+0100")
        self.arbitrer()
        self.assertIn("· témoins frais ·", self.lignes_de_journal()[0])

    def test_un_temoin_dont_le_message_porte_l_identifiant_dans_la_ligne_de_session_compte(self):
        self.poser_un_temoin("alpha", "AbCd1234")
        self.valider("Reprise\n\nClaude-Session: https://claude.ai/code/session_01XYZAbCd1234", quand="2026-03-15T01:00:00+0100")
        self.arbitrer()
        self.assertIn("· témoins frais ·", self.lignes_de_journal()[0])


LIVRE = "2026-03-12T10:00:00+0100"   # le commit qui passe l'entrée en recette


class TestCheckpointEnRetard(CasArbitre):
    """La date d'acceptation est celle du commit qui passe l'entrée en recette, jamais « recette-le: »."""
    cites = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))

    def en_recette(self, *supplement: str, quand: str = LIVRE, message: str = "alpha-2 passe en recette", **cles):
        """Un commit daté qui met alpha-2 en recette (sans « recette-le: » : l'arbitre le pose), sans toucher au checkpoint."""
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Livré", statut="recette", module="module-a", **cles),
            *supplement,
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))
        self.valider(message, quand=quand)

    def test_un_chantier_passe_en_recette_apres_le_dernier_commit_du_checkpoint_est_detecte(self):
        self.en_recette()  # le checkpoint d'alpha date du 1er mars, le passage en recette du 12
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c9-checkpoint-alpha-20260315"])
        c = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]
        self.assertEqual(c["pour"], "Opus-CdP-Alpha")
        self.assertIn("alpha : alpha-2 est en recette depuis le 2026-03-12, "
                      "le checkpoint n'a pas été touché depuis le 2026-03-01", c["mesure"])
        self.assertIn("Reprendre ton checkpoint", c["mesure"])
        self.assertNotIn("Citer chaque chantier", c["mesure"], "aucune ligne du contrôle 9 : pas de consigne de citation")
        self.assertRegex(self.lignes_de_journal()[0], r"· 1 écart · 1 constat nouveau · .*· checkpoints : alpha · socle")

    def test_pas_d_ecart_si_le_checkpoint_a_ete_touche_apres_la_recette(self):
        self.en_recette()
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint à jour", quand="2026-03-13T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])
        self.assertIn("· 0 écart ·", self.lignes_de_journal()[0])

    def test_le_meme_jour_n_est_pas_un_retard(self):
        self.en_recette()
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint du jour de la recette", quand="2026-03-12T23:00:00+0100")
        self.assertEqual(self.arbitrer().code, 0)

    def test_le_retard_se_groupe_avec_les_lignes_du_controle_9_du_meme_domaine(self):
        self.en_recette(bloc("alpha-3", statut="a-venir", module="module-a"), message="alpha-3 n'est pas cité")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c9-checkpoint-alpha-20260315"])
        mesure = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]["mesure"]
        self.assertIn("alpha : alpha-3 (a-venir) n'est pas cité au checkpoint ; alpha : alpha-2 est en recette", mesure)

    def test_un_message_pour_un_cdp_n_est_pas_un_sujet_du_domaine(self):
        self.en_recette(pour="Opus-CdP-Alpha", message="un message en recette")
        self.assertEqual(self.arbitrer().code, 0)

    def test_pas_de_doublon_au_passage_suivant(self):
        self.en_recette()
        self.arbitrer()
        apres = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer(date="2026-03-16 06:43")
        self.assertEqual(sortie.code, 0, sortie.stdout)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), apres)

    # ── la date d'acceptation vient de l'historique ──

    def test_le_jour_J_puis_J_plus_1_puis_J_plus_2_ne_fait_pas_de_fausse_alerte(self):
        """J : le CdP passe l'entrée en recette et rafraîchit son checkpoint. J+1 : l'arbitre pose « recette-le: ».
        J+2 : « recette-le: » (J+1) suit le dernier commit du checkpoint (J) : plus aucune alerte."""
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Livré", statut="a-venir", module="module-a"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1", "alpha-2"))
        self.valider("alpha-2 ouvert", quand="2026-03-10T10:00:00+0100")
        self.en_recette(quand=LIVRE, message="J : alpha-2 en recette")
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nalpha-2 livré.\n")
        self.valider("J : checkpoint rafraîchi", quand="2026-03-12T10:05:00+0100")
        self.assertNotIn("recette-le:", self.lire("Dossier/chantiers.yaml"))

        sortie = self.arbitrer(date="2026-03-13 06:43")                      # J+1
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertIn("  statut: recette\n  recette-le: 2026-03-13\n", self.lire("Dossier/chantiers.yaml"))
        self.valider("Arbitre J+1", quand="2026-03-13T06:50:00+0100")

        sortie = self.arbitrer(date="2026-03-14 06:43")                      # J+2
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])
        self.assertIn("· 0 écart ·", self.lignes_de_journal()[-1])
        self.assertNotIn("Checkpoint en retard", sortie.stdout)

    def test_le_recette_le_pose_a_la_main_n_est_pas_la_date_d_acceptation(self):
        self.en_recette(recette_le="2026-03-12", quand="2026-03-02T10:00:00+0100")  # en recette le 2, daté du 12 à la main
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint à jour", quand="2026-03-05T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])

    def test_la_date_est_celle_du_passage_pas_celle_des_commits_suivants_du_fichier(self):
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint à jour", quand="2026-03-11T10:00:00+0100")
        self.en_recette(message="alpha-2 en recette")
        note = bloc("note-1", statut="a-cadrer", module="module-b", pour="Opus-CdP-Beta")
        self.en_recette(note, quand="2026-03-13T10:00:00+0100", message="un message pour beta")
        self.en_recette(note, bloc("note-2", statut="a-cadrer", module="module-b", pour="Opus-CdP-Beta"),
                        quand="2026-03-14T10:00:00+0100", message="un autre message")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        mesure = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]["mesure"]
        self.assertIn("alpha : alpha-2 est en recette depuis le 2026-03-12, "
                      "le checkpoint n'a pas été touché depuis le 2026-03-11", mesure)

    def test_une_serie_interrompue_repart_au_dernier_passage_en_recette(self):
        self.en_recette(quand="2026-03-05T10:00:00+0100", message="alpha-2 en recette")
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint à jour", quand="2026-03-08T10:00:00+0100")
        self.ecrire_chantiers(bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
                              bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))
        self.valider("alpha-2 archivé", quand="2026-03-09T10:00:00+0100")
        self.en_recette(quand=LIVRE, message="alpha-2 revient en recette")  # sans l'interruption, il serait en recette depuis le 5
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        mesure = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]["mesure"]
        self.assertIn("alpha : alpha-2 est en recette depuis le 2026-03-12, "
                      "le checkpoint n'a pas été touché depuis le 2026-03-08", mesure)

    def test_deux_entrees_ont_chacune_leur_date(self):
        self.en_recette(quand="2026-03-09T10:00:00+0100", message="alpha-2 en recette")
        self.ecrire(f"depot/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha : checkpoint à jour", quand="2026-03-10T10:00:00+0100")
        self.en_recette(bloc("alpha-3", titre="Livré aussi", statut="recette", module="module-a"),
                        quand=LIVRE, message="alpha-3 en recette")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        mesure = self.par_id()["arbitre-c9-checkpoint-alpha-20260315"]["mesure"]
        self.assertIn("alpha-3 est en recette depuis le 2026-03-12", mesure)
        self.assertNotIn("alpha-2 est en recette", mesure, "alpha-2 est en recette depuis le 9, avant le checkpoint du 10")

    def retard_dans_un_clone(self, profondeur: int) -> str:
        """Le résumé d'un passage dans un clone peu profond : tout ce qui précède son premier commit est inconnu."""
        clone = self.sous_dossier("court") / f"profondeur{profondeur}"
        subprocess.run(["git", "clone", "-q", "--depth", str(profondeur), f"file://{self.depot}", str(clone)],
                       check=True, capture_output=True)
        sortie = self.lancer(clone / "Methode" / "arbitre.py", *self.options(), "--date", PASSAGE, cwd=clone)
        self.assertIn(sortie.code, (0, 1), sortie.stdout + sortie.stderr)
        return sortie.stdout

    def test_un_historique_qui_contient_le_passage_suffit_a_la_preuve(self):
        self.en_recette()  # deux commits : la base, puis le passage en recette
        self.assertIn("Checkpoint en retard · alpha", self.retard_dans_un_clone(2))

    def test_un_historique_trop_court_ne_prouve_rien_et_ne_fait_aucune_ligne(self):
        self.en_recette()  # un seul commit lu : l'entrée y est déjà en recette
        self.assertNotIn("Checkpoint en retard", self.retard_dans_un_clone(1))


class TestCheckpointSansPreuve(CasArbitre):
    """Une entrée déjà en recette au premier commit de l'historique : pas de preuve de son passage, pas d'alerte."""
    cites = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Livré", statut="recette", module="module-a", recette_le="2026-03-12"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"))

    def test_une_entree_deja_en_recette_au_premier_commit_ne_fait_aucune_ligne(self):
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])
        self.assertIn("· 0 écart ·", self.lignes_de_journal()[0])
        self.assertNotIn("Checkpoint en retard", sortie.stdout)

    def test_une_version_introuvable_du_fichier_arrete_la_preuve(self):
        """Le fichier sort du dépôt, puis revient en recette : la version manquante ne prouve rien."""
        self.git("rm", "-q", "--cached", "Dossier/chantiers.yaml")
        self.git("commit", "-q", "-m", "le fichier sort de l'index", quand="2026-03-02T10:00:00+0100")
        self.valider("le fichier revient", quand="2026-03-03T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])

    def test_un_fichier_sans_historique_ne_fait_aucune_ligne(self):
        """Le fichier existe sur le disque mais n'est plus (ou pas encore) dans le dépôt : rien à lire."""
        self.git("rm", "-q", "--cached", "Dossier/chantiers.yaml")
        self.git("commit", "-q", "-m", "le fichier sort du dépôt", quand="2026-03-02T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [])


class TestNormalisation(CasArbitre):
    def test_la_normalisation_se_fait_avant_le_controle(self):
        texte = self.lire("Dossier/chantiers.yaml").replace(
            "titre: Premier", "titre: Premier : un titre avec deux-points")
        self.ecrire("depot/Dossier/chantiers.yaml", texte)
        self.valider("une valeur non conforme")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), [], "le contrôle 11 ne voit plus rien : la valeur est normalisée avant")
        self.assertIn('  titre: "Premier : un titre avec deux-points"', self.lire("Dossier/chantiers.yaml"))
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : vivants conformes, 1 valeur(s) normalisée(s)")
        controle = self.lancer(self.depot / "Methode" / "verifier_vivants.py", "--chantiers", "Dossier/chantiers.yaml",
                               "--registre", "Dossier/registre.md", cwd=self.depot)
        self.assertEqual(controle.verdict(11), "OK")

    def test_une_valeur_non_normalisable_reste_un_ecart_du_controle_11_pour_le_coordinateur(self):
        texte = self.lire("Dossier/chantiers.yaml").replace("titre: Premier", "titre: Prem\x01ier")
        self.ecrire("depot/Dossier/chantiers.yaml", texte)
        self.valider("un caractère de contrôle")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-c11-format-chantiers"])
        c = self.par_id()["arbitre-c11-format-chantiers"]
        self.assertEqual((c["pour"], c["module"]), ("Opus-Coordination", "methode"))


class TestArchivage(CasArbitre):
    def chantiers_conformes(self):
        self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("beta-1", titre="Autre", statut="a-venir", module="module-b"),
            bloc("alpha-vieux", titre="Livré il y a huit jours", statut="recette", module="module-a",
                 recette_le="2026-03-07"),
            bloc("beta-neuf", titre="Livré hier", statut="recette", module="module-b"))

    cites = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def test_l_archivage_date_et_sort_et_le_journal_et_le_commit_le_disent(self):
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha à jour", quand="2026-03-14T10:00:00+0100")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        archive = self.lire("Dossier/Archives/CHANTIERS_2026-03.yaml")
        self.assertIn("- id: alpha-vieux", archive)
        chantiers = self.lire("Dossier/chantiers.yaml")
        self.assertNotIn("alpha-vieux", chantiers)
        self.assertIn("  statut: recette\n  recette-le: 2026-03-15\n", chantiers)
        self.assertIn("· archivage : 1 daté(s), 1 archivé(s) ·", self.lignes_de_journal()[0])
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : vivants conformes, 1 daté(s), 1 archivé(s)")
        self.assertIn("Dossier/Archives/", " ".join(self.modifies()))
        self.assertIn("Archivage · 1 daté(s), 1 archivé(s)", sortie.stdout)

    def test_le_tableau_est_regenere_quand_l_archivage_change_chantiers_yaml(self):
        self.ecrire("depot/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "\nMis à jour.\n")
        self.valider("Alpha à jour", quand="2026-03-14T10:00:00+0100")
        avant = self.lire("Dossier/chantiers.json")
        self.arbitrer()
        self.assertNotEqual(self.lire("Dossier/chantiers.json"), avant)
        self.assertNotIn("alpha-vieux", self.lire("Dossier/chantiers.json"))
        controle = self.lancer(self.depot / "Methode" / "verifier_vivants.py", "--chantiers", "Dossier/chantiers.yaml",
                               "--registre", "Dossier/registre.md", "--archives", "Dossier/Archives",
                               "--tableau", "Dossier/chantiers.html", "--generateur", "Methode/generer_tableau.py",
                               cwd=self.depot)
        self.assertEqual(controle.verdict(6), "OK", controle.stdout)

    def test_une_date_illisible_est_un_constat_pour_le_coordinateur(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                              bloc("beta-1", statut="a-venir", module="module-b"),
                              bloc("alpha-mal", statut="recette", module="module-a", recette_le="hier"))
        self.valider("une date illisible")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.arbitres(), ["arbitre-ca-archivage-alpha-mal"])
        c = self.par_id()["arbitre-ca-archivage-alpha-mal"]
        self.assertEqual((c["pour"], c["module"]), ("Opus-Coordination", "module-a"))
        self.assertIn("alpha-mal : recette-le illisible", c["mesure"])


class TestTableauSeulementSiChange(CasArbitre):
    def test_un_passage_qui_ne_change_pas_chantiers_yaml_ne_touche_pas_au_tableau(self):
        avant = (self.lire("Dossier/chantiers.html"), self.lire("Dossier/chantiers.json"))
        self.arbitrer(date="2026-03-15 06:43")
        self.arbitrer(date="2026-03-16 06:43")
        self.assertEqual((self.lire("Dossier/chantiers.html"), self.lire("Dossier/chantiers.json")), avant)
        self.assertEqual(self.modifies(), ["Methode/ARBITRE_JOURNAL.md"])

    def test_un_tableau_perime_est_signale_puis_regenere_parce_que_chantiers_yaml_a_change(self):
        self.ecrire("depot/Dossier/chantiers.json", "{}")
        self.valider("données périmées", tableau=False)
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 1, sortie.stdout)
        self.assertEqual(self.arbitres(), ["arbitre-c6-tableau"])
        self.assertNotEqual(self.lire("Dossier/chantiers.json"), "{}")
        self.assertIn("arbitre-c6-tableau", self.lire("Dossier/chantiers.json"))

    def test_sans_tableau_le_script_n_en_ecrit_pas(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="en-vol", module="module-a"),
                              bloc("beta-1", statut="a-venir", module="module-b"))
        self.valider("alpha-1 en vol sans cdp")
        avant = self.lire("Dossier/chantiers.json")
        options = [o for o in self.options() if o not in ("--tableau", "Dossier/chantiers.html", "--generateur",
                                                          "Methode/generer_tableau.py")]
        sortie = self.arbitrer(options=options)
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.json"), avant)


class TestFichierManquant(CasArbitre):
    def test_un_fichier_qui_manque_rend_2_et_ecrit_le_journal_seul(self):
        os.remove(self.depot / "Dossier" / "registre.md")
        avant = self.lire("Dossier/chantiers.yaml")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2, sortie.stdout + sortie.stderr)
        self.assertIn("fichier introuvable : Dossier/registre.md", sortie.stderr)
        self.assertEqual(self.lire("Dossier/chantiers.yaml"), avant)
        self.assertEqual(self.modifies(), ["Dossier/registre.md", "Methode/ARBITRE_JOURNAL.md"])
        self.assertEqual(self.lignes_de_journal(), ["- 2026-03-15 06:43 · contrôle impossible : Dossier/registre.md"])
        self.assertEqual(self.commit_du_passage(sortie), "Arbitre 2026-03-15 : contrôle impossible")

    def test_un_dossier_d_archives_qui_manque_rend_2(self):
        shutil.rmtree(self.depot / "Dossier" / "Archives")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2)
        self.assertIn("contrôle impossible : Dossier/Archives", self.lignes_de_journal()[0])

    def test_un_script_voisin_qui_manque_rend_2(self):
        os.remove(self.depot / "Methode" / "verifier_vivants.py")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2)
        self.assertIn("contrôle impossible : verifier_vivants.py", self.lignes_de_journal()[0])

    def test_hors_d_un_depot_git_rend_2(self):
        shutil.rmtree(self.depot / ".git")
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2)
        self.assertIn("contrôle impossible : dépôt git", self.lignes_de_journal()[0])

    def test_un_script_qui_echoue_rend_2(self):
        self.ecrire("depot/Methode/generer_tableau.py", "import sys\nsys.exit(3)\n")
        self.ecrire_chantiers(bloc("alpha-1", statut="en-vol", module="module-a"),
                              bloc("beta-1", statut="a-venir", module="module-b"))
        self.valider("un générateur cassé", tableau=False)
        sortie = self.arbitrer()
        self.assertEqual(sortie.code, 2, sortie.stdout + sortie.stderr)
        self.assertRegex(self.lignes_de_journal()[-1], r"contrôle impossible : ")


class TestSocle(CasArbitre):
    def test_le_socle_du_journal_somme_la_methode_la_fiche_et_les_checkpoints(self):
        self.ecrire("depot/Methode/METHODE.md", "x" * 3000)
        for chemin in CHECKPOINTS.values():
            self.ecrire(f"depot/{chemin}", "x" * 1000)
        self.ecrire("depot/Dossier/FICHE.md", "x" * 2000)
        self.valider("des tailles connues")
        self.arbitrer(options=self.options(methode=True) + ["--fiche", "Dossier/FICHE.md"])
        # 3000 + 2000 + 3 × 1000 = 8000 octets = 7,8 Ko, arrondi à 8
        self.assertTrue(self.lignes_de_journal()[0].endswith(" · socle : 8 Ko"), self.lignes_de_journal()[0])

    def test_sans_methode_ni_fiche_le_socle_ne_compte_que_les_checkpoints(self):
        for chemin in CHECKPOINTS.values():
            self.ecrire(f"depot/{chemin}", "x" * 1024)
        self.valider("trois checkpoints de 1 Ko")
        self.arbitrer(options=self.options(methode=False))
        self.assertTrue(self.lignes_de_journal()[0].endswith(" · socle : 3 Ko"), self.lignes_de_journal()[0])

    def test_un_fichier_donne_deux_fois_ne_compte_qu_une_fois(self):
        for chemin in CHECKPOINTS.values():
            self.ecrire(f"depot/{chemin}", "x" * 1024)
        self.valider("trois checkpoints de 1 Ko")
        self.arbitrer(options=self.options(methode=False, fiche=True))  # la fiche est le checkpoint d'alpha
        self.assertTrue(self.lignes_de_journal()[0].endswith(" · socle : 3 Ko"), self.lignes_de_journal()[0])


class TestAppelsInvalides(CasArbitre):
    def test_une_option_obligatoire_manque(self):
        options = self.options()
        i = options.index("--registre")
        sortie = self.arbitrer(options=options[:i] + options[i + 2:])
        self.assertEqual(sortie.code, 2)
        self.assertIn("argument manquant : --registre", sortie.stderr)
        self.assertEqual(self.lignes_de_journal(), [])

    def test_tableau_et_generateur_vont_ensemble(self):
        options = [o for o in self.options() if o not in ("--generateur", "Methode/generer_tableau.py")]
        sortie = self.arbitrer(options=options)
        self.assertEqual(sortie.code, 2)
        self.assertIn("--tableau et --generateur vont ensemble", sortie.stderr)

    def test_une_option_inconnue(self):
        sortie = self.arbitrer("--bidule", "1")
        self.assertEqual(sortie.code, 2)
        self.assertIn("argument inconnu : --bidule", sortie.stderr)

    def test_une_date_mal_formee(self):
        sortie = self.arbitrer(date="15/03/2026")
        self.assertEqual(sortie.code, 2)
        self.assertIn("--date : AAAA-MM-JJ HH:MM attendu", sortie.stderr)


class TestWorkflow(unittest.TestCase):
    def texte(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")

    def test_le_modele_porte_le_declencheur_les_droits_et_le_script(self):
        texte = self.texte()
        for attendu in ("schedule:", 'cron: "42 5 * * *"', "workflow_dispatch:", "contents: write", "concurrency:",
                        "fetch-depth: 300", "actions/checkout@v7", "actions/setup-python@v7", 'python-version: "3.12"',
                        "github-actions[bot]", "git pull --rebase", "GITHUB_STEP_SUMMARY", "sed -n 's/^Commit : //p'"):
            self.assertIn(attendu, texte)

    def test_il_ne_vit_pas_dans_le_dossier_github_du_package(self):
        self.assertFalse((MODELES.parent / ".github" / "workflows" / "arbitre.yml").exists())

    @unittest.skipIf(pyyaml is None, "PyYAML absent")
    def test_le_modele_est_du_yaml_valide_et_sa_structure_est_celle_attendue(self):
        document = pyyaml.safe_load(self.texte())
        declencheurs = document.get("on", document.get(True))  # YAML 1.1 lit « on » comme un booléen
        self.assertIn("schedule", declencheurs)
        self.assertIn("workflow_dispatch", declencheurs)
        self.assertEqual(document["permissions"], {"contents": "write"})
        self.assertEqual(document["concurrency"]["cancel-in-progress"], False)
        pas = document["jobs"]["arbitre"]["steps"]
        self.assertEqual(pas[0]["with"]["fetch-depth"], 300)
        self.assertEqual(pas[1]["with"]["python-version"], "3.12")
        for variable in ("SCRIPT", "CHANTIERS", "REGISTRE", "ARCHIVES", "DOMAINES", "JOURNAL_ARBITRE"):
            self.assertIn(variable, document["env"])

    def test_la_variable_registre_depuis_est_facultative_et_vide_par_defaut(self):
        texte = self.texte()
        self.assertRegex(texte, r'(?m)^  REGISTRE_DEPUIS: ""$')
        self.assertIn('if [ -n "$REGISTRE_DEPUIS" ]; then args+=(--registre-depuis "$REGISTRE_DEPUIS"); fi', texte)
        self.assertLess(texte.index("  FICHE:"), texte.index("  REGISTRE_DEPUIS:"))
        self.assertLess(texte.index("  REGISTRE_DEPUIS:"), texte.index("jobs:"))

    def test_chaque_chemin_a_sa_variable_en_tete_du_fichier(self):
        texte = self.texte()
        for variable in ("CHANTIERS", "REGISTRE", "ARCHIVES", "DOMAINES", "JOURNAL_ARBITRE", "TABLEAU", "GENERATEUR",
                         "JOURNAL_PLAN", "METHODE", "FICHE", "SCRIPT"):
            self.assertRegex(texte, rf"(?m)^  {variable}: ")


if __name__ == "__main__":
    unittest.main()
