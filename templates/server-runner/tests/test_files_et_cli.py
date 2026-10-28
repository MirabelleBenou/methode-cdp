"""T17 (les deux files), la ligne de commande, la configuration invalide, les comptes rendus « en cours »."""

import json
import os
import subprocess
import sys
import unittest

from outils import RACINE, Env, ecrire, lire

from deployeur import config, registre


def lancer_cli(*args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run([sys.executable, "-m", "deployeur"] + list(args), cwd=RACINE, env=e,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


class TestDeuxFiles(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)
        self.reg = registre.Registre(self.env.etat_dir)
        self.reg.preparer()

    def test_t17_le_verrou_de_fichiers_pris_n_empeche_pas_deploiement(self):
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.ordre("2026-10-27-02", action="fichiers",
                       operations=[{"operation": "creer-dossier", "zone": "fichiers", "chemin": "nouveau"}])
        with self.reg.verrou("fichiers") as v:
            self.assertTrue(v.pris)
            self.assertEqual(self.env.lancer("deploiement"), 0)
            self.assertEqual(self.env.statut("2026-10-27-01"), "réussi")
            # la file fichiers trouve son verrou pris : elle sort sans rien faire
            self.assertEqual(self.env.lancer("fichiers"), 0)
            self.assertTrue(any("verrou pris" in l for l in self.env.sortie), self.env.sortie)
            self.assertIsNone(self.env.resultat("2026-10-27-02"))
            self.assertFalse(os.path.exists(os.path.join(self.env.zone_fichiers, "nouveau")))
        self.env.lancer("fichiers")
        self.assertEqual(self.env.statut("2026-10-27-02"), "réussi")

    def test_t17_le_verrou_de_deploiement_pris_n_empeche_pas_fichiers(self):
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.ordre("2026-10-27-02", action="fichiers",
                       operations=[{"operation": "creer-dossier", "zone": "fichiers", "chemin": "nouveau"}])
        with self.reg.verrou("deploiement") as v:
            self.assertTrue(v.pris)
            self.env.lancer("fichiers")
            self.assertEqual(self.env.statut("2026-10-27-02"), "réussi")
            self.env.lancer("deploiement")
            self.assertIsNone(self.env.resultat("2026-10-27-01"))
        self.env.lancer("deploiement")
        self.assertEqual(self.env.statut("2026-10-27-01"), "réussi")

    def test_t17_chaque_file_ne_joue_que_ses_ordres(self):
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.ordre("2026-10-27-02", action="fichiers",
                       operations=[{"operation": "creer-dossier", "zone": "fichiers", "chemin": "nouveau"}])
        self.env.lancer("fichiers")
        self.assertIsNone(self.env.resultat("2026-10-27-01"))
        self.assertEqual(self.env.statut("2026-10-27-02"), "réussi")
        self.assertEqual(self.env.appels(), [])
        self.env.lancer("deploiement")
        self.assertEqual(self.env.statut("2026-10-27-01"), "réussi")
        journal_f = json.loads(lire(os.path.join(self.env.etat_dir, "journal-fichiers.json")))["ordres"]
        self.assertEqual(list(journal_f), ["2026-10-27-02"])

    def test_deux_processus_reels_le_second_sort_sans_rien_faire(self):
        env = self.env
        env.ordre("2026-10-27-01", action="etat")
        chemin = env.ecrire_config()
        with self.reg.verrou("deploiement") as v:
            self.assertTrue(v.pris)
            r = lancer_cli("--file", "deploiement", "--config", chemin)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("verrou pris", r.stdout)
        self.assertIsNone(env.resultat("2026-10-27-01"))

    def test_une_file_fichiers_arretee_refuse_ses_ordres_et_reprendre_file_la_rouvre(self):
        self.reg.arreter("fichiers", "2026-10-26-01", "test", "2026-10-26T00:00:00Z")
        ops = [{"operation": "creer-dossier", "zone": "fichiers", "chemin": "nouveau"}]
        self.assertEqual(self.env.jouer("2026-10-27-01", action="fichiers", operations=ops), "refusé")
        self.assertFalse(os.path.exists(os.path.join(self.env.zone_fichiers, "nouveau")))
        self.assertEqual(self.env.jouer("2026-10-27-02", action="reprendre-file", file="fichiers", go="ok"), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-03", action="fichiers", operations=ops), "réussi")


class TestLigneDeCommande(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)

    def test_verifier_une_configuration_valide(self):
        r = lancer_cli("--verifier", "--config", self.env.ecrire_config())
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "configuration valide"))

    def test_verifier_la_configuration_d_exemple(self):
        r = lancer_cli("--verifier", "--config", os.path.join(RACINE, "config.exemple.json"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_configuration_invalide_refuse_de_tourner(self):
        self.env.dict_config["zones"]["fichiers"]["chemin"] = "/etc"
        chemin = self.env.ecrire_config()
        self.env.ordre("2026-10-27-01", action="etat")
        r = lancer_cli("--file", "deploiement", "--config", chemin)
        self.assertEqual(r.returncode, 2)
        self.assertIn("configuration invalide", r.stderr)
        self.assertIsNone(self.env.resultat("2026-10-27-01"))
        self.assertEqual(self.env.appels(), [])
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "journal-deploiement.json")))

    def test_configuration_introuvable_ou_illisible(self):
        r = lancer_cli("--verifier", "--config", self.env.racine + "/nulle.json")
        self.assertEqual(r.returncode, 2)
        ecrire(self.env.racine + "/x.json", "{pas du json")
        self.assertEqual(lancer_cli("--verifier", "--config", self.env.racine + "/x.json").returncode, 2)

    def test_file_obligatoire_et_valeurs_permises(self):
        chemin = self.env.ecrire_config()
        self.assertEqual(lancer_cli("--config", chemin).returncode, 2)
        self.assertEqual(lancer_cli("--file", "autre", "--config", chemin).returncode, 2)

    def test_un_passage_complet_par_la_ligne_de_commande(self):
        self.env.ordre("2026-10-27-01", action="etat")
        r = lancer_cli("--file", "deploiement", "--config", self.env.ecrire_config())
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(self.env.statut("2026-10-27-01"), "réussi")
        self.assertIn("passage terminé", r.stdout)
        self.assertEqual(self.env.interdits(), [])

    def test_une_erreur_de_depot_d_ordres_rend_un_code_non_nul_sans_rien_jouer(self):
        self.env.dict_config["depot_ordres"]["url"] = "file://" + self.env.racine + "/nulle-part.git"
        r = lancer_cli("--file", "deploiement", "--config", self.env.ecrire_config())
        self.assertEqual(r.returncode, 1)
        self.assertIn("inaccessible", r.stdout)


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)

    def refuse(self, modif, motif):
        d = json.loads(json.dumps(self.env.dict_config))
        modif(d)
        with self.assertRaises(config.ErreurConfig) as cm:
            config.valider(d)
        self.assertIn(motif, " ".join(cm.exception.problemes))

    def test_champs_manquants_ou_mal_types(self):
        self.refuse(lambda d: d.pop("git"), "git")
        self.refuse(lambda d: d["application"].pop("projet"), "projet")
        self.refuse(lambda d: d["application"].update(dossier="relatif"), "dossier")
        self.refuse(lambda d: d["application"].update(tables_histoire=[]), "tables_histoire")
        self.refuse(lambda d: d["application"].update(tables_histoire="membres"), "tables_histoire")
        self.refuse(lambda d: d["application"].update(tables_histoire=["a b"]), "tables_histoire")
        self.refuse(lambda d: d["application"].update(url_sante="ftp://x"), "url_sante")
        self.refuse(lambda d: d["application"].update(sauvegardes_garder="dix"), "sauvegardes_garder")
        self.refuse(lambda d: d["application"].update(delai_sante_s=0), "delai_sante_s")
        self.refuse(lambda d: d.pop("zones"), "zones")
        self.refuse(lambda d: d["suites"]["suite-a"].update(chemin="../x"), "chemin")
        self.refuse(lambda d: d["depot_ordres"].update(url="--upload-pack=x"), "depot_ordres.url")
        self.refuse(lambda d: d["git"].update(cle_ordres="relative"), "cle_ordres")
        self.refuse(lambda d: d.update(depots_publics=["pas-un-depot"]), "depots_publics")
        self.refuse(lambda d: d.update(repertoire_etat="relatif"), "repertoire_etat")

    def test_une_configuration_non_objet_est_refusee(self):
        with self.assertRaises(config.ErreurConfig):
            config.valider([])

    def test_defauts_et_valeur_minimale_de_sauvegardes(self):
        cfg = self.env.cfg()
        self.assertEqual(config.garder_effectif(cfg.application._replace(sauvegardes_garder=1)), 3)
        self.assertEqual(config.garder_effectif(cfg.application._replace(sauvegardes_garder=10)), 10)
        self.assertIn(".env", cfg.application.chemins_proteges)
        self.assertIn("backups/", cfg.application.chemins_proteges)

    def test_chemins_proteges_supplementaires(self):
        d = json.loads(json.dumps(self.env.dict_config))
        d["application"]["chemins_proteges"] = ["certificats/"]
        cfg = config.valider(d)
        self.assertEqual(cfg.application.chemins_proteges[-1], "certificats/")
        self.assertEqual(cfg.application.chemins_proteges[:2], [".env", "backups/"])


class TestEnCours(unittest.TestCase):
    def test_un_compte_rendu_en_cours_est_pousse_pendant_une_operation_longue(self):
        env = Env(self)
        env.dict_config["intervalle_en_cours_s"] = 0.01
        z = env.zone_fichiers
        for i in range(30):
            ecrire(os.path.join(z, "src", "f%02d" % i), "x" * 1000)
        env.ordre("2026-10-27-01", action="fichiers",
                  operations=[{"operation": "copier", "zone": "fichiers", "de": "src", "vers": "copie"}])
        from unittest import mock
        import time
        from deployeur import fichiers
        vrai = fichiers._copier_fichier

        def lent(*a, **k):
            time.sleep(0.03)
            return vrai(*a, **k)
        with mock.patch.object(fichiers, "_copier_fichier", lent):
            env.lancer("fichiers")
        self.assertEqual(env.statut("2026-10-27-01"), "réussi")
        pushes = [l for l in env.sortie if "poussé" in l]
        self.assertGreater(len(pushes), 1)         # au moins un « en cours » avant le final
        log = subprocess.run(["git", "log", "--format=%s", "--", "resultats/2026-10-27-01.md"], cwd=env.ordres_w,
                             stdout=subprocess.PIPE, universal_newlines=True).stdout
        env.resultat("2026-10-27-01")
        log = subprocess.run(["git", "log", "--format=%s", "--", "resultats/2026-10-27-01.md"], cwd=env.ordres_w,
                             stdout=subprocess.PIPE, universal_newlines=True).stdout.splitlines()
        self.assertIn("Compte rendu 2026-10-27-01 : en cours", log)
        self.assertEqual(log[0], "Compte rendu 2026-10-27-01 : réussi")

    def test_sans_intervalle_pas_de_compte_rendu_intermediaire(self):
        env = Env(self)
        env.ordre("2026-10-27-01", action="fichiers",
                  operations=[{"operation": "creer-dossier", "zone": "fichiers", "chemin": "x"}])
        env.lancer("fichiers")
        env.resultat("2026-10-27-01")
        log = subprocess.run(["git", "log", "--format=%s", "--", "resultats/2026-10-27-01.md"], cwd=env.ordres_w,
                             stdout=subprocess.PIPE, universal_newlines=True).stdout.splitlines()
        self.assertEqual(log, ["Compte rendu 2026-10-27-01 : réussi"])


class TestPushDiffere(unittest.TestCase):
    def test_un_push_refuse_est_retente_au_passage_suivant(self):
        env = Env(self)
        env.ordre("2026-10-27-01", action="etat")
        # le dépôt distant refuse les pushes (hook pre-receive)
        hook = os.path.join(env.ordres_remote, "hooks", "pre-receive")
        ecrire(hook, "#!/bin/sh\nexit 1\n", executable=True)
        env.lancer()
        self.assertTrue(any("en échec" in l for l in env.sortie), env.sortie)
        self.assertIsNone(env.resultat("2026-10-27-01"))            # rien de poussé
        journal = json.loads(lire(os.path.join(env.etat_dir, "journal-deploiement.json")))["ordres"]
        self.assertEqual(journal["2026-10-27-01"]["statut"], "réussi")
        os.remove(hook)
        n = len(env.appels())
        env.lancer()
        self.assertEqual(env.statut("2026-10-27-01"), "réussi")     # retenté, sans rejouer l'ordre
        self.assertEqual(len(env.appels()), n)

    def test_la_suite_se_joue_malgre_un_echec_de_push(self):
        env = Env(self)
        env.ordre("2026-10-27-01", action="etat")
        env.ordre("2026-10-27-02", action="etat")
        hook = os.path.join(env.ordres_remote, "hooks", "pre-receive")
        ecrire(hook, "#!/bin/sh\nexit 1\n", executable=True)
        env.lancer()
        journal = json.loads(lire(os.path.join(env.etat_dir, "journal-deploiement.json")))["ordres"]
        self.assertEqual(sorted(journal), ["2026-10-27-01", "2026-10-27-02"])


if __name__ == "__main__":
    unittest.main()
