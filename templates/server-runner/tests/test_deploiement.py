"""T2 à T10, T12, T15, T16 : les ordres de la file ``deploiement`` sur les doublures."""

import json
import os
import re
import unittest
from unittest import mock

from outils import Env, SH_DUMP, SH_LIRE, ecrire, lire

from deployeur import application

GO = "go de test"
A_PREFIXE = ["compose", "-p", "monprojet", "--project-directory"]


def base_compose(env):
    return ["compose", "-p", "monprojet", "--project-directory", env.app, "-f", env.app + "/docker-compose.yml"]


class Base(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)

    def verifier_nouveau_servi(self, revision):
        """Addendum 2 : le nouveau commit (1.0056) est « servi », l'ancien (1.0055) « précédent », manifeste et archive gardés."""
        etat = self.env.application()
        self.assertEqual(etat["servi"]["commit"], self.commit_b)
        self.assertEqual(etat["servi"]["version"], "1.0056")
        self.assertEqual(etat["servi"]["revision"], revision)
        self.assertEqual(etat["precedent"]["commit"], self.env.commit_a)
        self.assertEqual(etat["precedent"]["version"], "1.0055")
        self.assertEqual(etat["precedent"]["revision"], "0039")
        self.assertEqual(etat["historique"][0], self.commit_b)
        self.assertTrue(os.path.isfile(os.path.join(self.env.etat_dir, "archives", self.commit_b + ".tar")))
        manifeste = json.loads(lire(os.path.join(self.env.etat_dir, "manifestes", self.commit_b + ".json")))
        self.assertIn("app/nouveau.py", manifeste["fichiers"])

    def deployer_b(self, ident="2026-10-27-02", version="1.0056", **plus):
        self.commit_b = self.env.nouveau_commit_b(version, **plus)
        return self.env.jouer(ident, action="deployer-application", commit=self.commit_b, version=version, go=GO)

    def mettre_pret(self):
        self.assertEqual(self.env.adopter(), "réussi")
        self.env.vider_appels()


class TestAdopter(Base):
    def test_t15_tous_identiques_enregistre_le_commit_servi(self):
        self.assertEqual(self.env.adopter(), "réussi")
        servi = self.env.servi()
        self.assertEqual(servi["commit"], self.env.commit_a)
        self.assertEqual(servi["version"], "1.0055")
        self.assertEqual(servi["revision"], "0039")
        r = self.env.resultat("2026-10-27-01")
        self.assertIn("inconnu.txt", r)            # fichiers hors archive listés
        self.assertTrue(os.path.isfile(os.path.join(self.env.etat_dir, "archives", self.env.commit_a + ".tar")))
        self.assertTrue(os.path.isfile(os.path.join(self.env.etat_dir, "manifestes", self.env.commit_a + ".json")))

    def test_t15_adopter_accepte_un_env_example_identique_au_disque(self):
        commit = self.env.commit_app({".env.example": "SECRET=\n"})
        self.env.poser_dossier(commit)                       # le disque porte exactement l'archive, .env.example compris
        self.assertEqual(self.env.jouer("2026-10-27-01", action="adopter", commit=commit), "réussi")
        self.assertEqual(self.env.servi()["commit"], commit)
        manifeste = json.loads(lire(os.path.join(self.env.etat_dir, "manifestes", commit + ".json")))
        self.assertIn(".env.example", manifeste["fichiers"])

    def test_t15_un_fichier_different_refuse(self):
        ecrire(os.path.join(self.env.app, "app", "main.py"), "print('modifie')\n")
        self.assertEqual(self.env.adopter(), "refusé")
        self.assertIn("app/main.py", self.env.resultat("2026-10-27-01"))
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "application.json")))

    def test_t15_bit_d_execution_different_refuse(self):
        os.chmod(os.path.join(self.env.app, "scripts", "start.sh"), 0o644)
        self.assertEqual(self.env.adopter(), "refusé")
        self.assertIn("bit d'exécution", self.env.resultat("2026-10-27-01"))

    def test_t15_fichier_absent_refuse(self):
        os.remove(os.path.join(self.env.app, "app", "ancien.py"))
        self.assertEqual(self.env.adopter(), "refusé")

    def test_t15_les_autres_bits_ne_comptent_pas(self):
        os.chmod(os.path.join(self.env.app, "app", "main.py"), 0o664)
        self.assertEqual(self.env.adopter(), "réussi")

    def test_t15_refuse_si_un_commit_servi_est_deja_connu(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="adopter", commit=self.env.commit_a), "refusé")

    def test_t15_aucun_geste_docker_en_ecriture(self):
        self.env.adopter()
        verbes = [a for a in self.env.appels() if a[0] != "exec" and a[0] != "inspect" and a[0] != "volume"]
        for a in verbes:
            self.assertEqual(a[7:], ["ps", "--format", "json"])
        self.assertEqual(self.env.interdits(), [])


class TestDeploiementReussi(Base):
    def test_t3_succes_complet(self):
        self.mettre_pret()
        proteges = {n: lire(os.path.join(self.env.app, n)) for n in (".env", ".env.SAVE", "inconnu.txt", "data/inconnu2.txt")}
        avant_backups = set(os.listdir(os.path.join(self.env.app, "backups")))
        self.assertEqual(self.deployer_b(), "réussi")

        # fichiers : posés, retiré (du manifeste précédent), inconnus et protégés intacts
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0056\n")
        self.assertEqual(lire(os.path.join(self.env.app, "app/main.py")), "print('b')\n")
        self.assertTrue(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertFalse(os.path.exists(os.path.join(self.env.app, "app/ancien.py")))
        for n, c in proteges.items():
            self.assertEqual(lire(os.path.join(self.env.app, n)), c, n)
        self.assertTrue(avant_backups <= set(os.listdir(os.path.join(self.env.app, "backups"))))
        # modes : 755 pour l'exécutable, 644 sinon
        self.assertTrue(os.stat(os.path.join(self.env.app, "scripts/start.sh")).st_mode & 0o100)
        self.assertEqual(os.stat(os.path.join(self.env.app, "app/nouveau.py")).st_mode & 0o777, 0o644)

        # sauvegarde prise et relue
        nouvelles = set(os.listdir(os.path.join(self.env.app, "backups"))) - avant_backups
        dumps = [n for n in nouvelles if n.endswith(".dump")]
        self.assertEqual(len(dumps), 1)
        self.assertRegex(dumps[0], r"^monprojet_deploiement-0039_\d{8}-\d{6}\.dump$")
        self.assertTrue(dumps[0].replace(".dump", "_ecussons.tar.gz") in nouvelles)
        self.assertGreater(os.path.getsize(os.path.join(self.env.app, "backups", dumps[0])), 0)

        # état
        servi = self.env.servi()
        self.assertEqual((servi["commit"], servi["version"]), (self.commit_b, "1.0056"))
        etat = json.loads(lire(os.path.join(self.env.etat_dir, "application.json")))
        self.assertEqual(etat["precedent"]["commit"], self.env.commit_a)
        self.assertEqual(etat["precedent"]["revision"], "0039")

        # la suite exacte des appels Docker
        b = base_compose(self.env)
        attendu = [
            b + ["ps", "--format", "json"],
            ["inspect", "monprojet-db-1"],
            ["volume", "inspect", "monprojet_pgdata"],
            ["volume", "inspect", "monprojet_images"],
            ["volume", "inspect", "monprojet_bruts"],
            ["exec", "-i", "monprojet-db-1", "sh", "-c", SH_LIRE],
            ["exec", "monprojet-db-1", "sh", "-c", SH_DUMP],
            ["exec", "-i", "monprojet-db-1", "pg_restore", "--list"],
            ["run", "--rm", "--network", "none", "--mount",
             "type=volume,src=monprojet_images,dst=/source,readonly", "postgres:16",
             "tar", "-czf", "-", "-C", "/source", "."],
            b + ["build", "app"],
            b + ["up", "-d", "--no-deps", "app"],
            None,   # logs (horodatage variable)
            ["exec", "-i", "monprojet-db-1", "sh", "-c", SH_LIRE],
        ]
        appels = self.env.appels()
        self.assertEqual(len(appels), len(attendu), appels)
        for a, e in zip(appels, attendu):
            if e is None:
                self.assertEqual(a[7:9], ["logs", "--no-color"])
                self.assertEqual(a[9], "--since")
                self.assertRegex(a[10], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
                self.assertEqual(a[11], "app")
            else:
                self.assertEqual(a, e)
        self.assertEqual(self.env.interdits(), [])
        # aucun appel vers le service db hors lecture/sauvegarde ; jamais build/up de db
        for a in appels:
            self.assertNotIn("db", a[7:] if a[0] == "compose" else [])

        # compte rendu : version, sauvegarde, comptes, révision
        r = self.env.resultat("2026-10-27-02")
        for morceau in ("1.0055", "1.0056", "0039", "TABLE DATA", "| membres (histoire) | 10 | 10 |"):
            self.assertIn(morceau, r)

    def test_t3_les_comptes_en_baisse_hors_histoire_sont_seulement_rapportes(self):
        self.mettre_pret()
        self.env.nouveau_commit_b()
        self.env.docker(apres={"tables": {"membres": 10, "evenements": 20, "autre": 1, "alembic_version": 1}})
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._dernier(),
                                        version="1.0056", go=GO), "réussi")
        r = self.env.resultat("2026-10-27-02")
        self.assertIn("| **autre** | **3** | **1** |", r)
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))

    def _dernier(self):
        from outils import git
        return git("rev-parse", "HEAD", cwd=self.env.src).strip()

    def test_t3_redeploiement_de_la_version_servie(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self.env.commit_a,
                                        version="1.0055", go=GO), "réussi")
        etat = json.loads(lire(os.path.join(self.env.etat_dir, "application.json")))
        self.assertEqual(etat["precedent"]["commit"], self.env.commit_a)

    def test_t3_un_redeploiement_garde_le_vrai_precedent(self):
        self.mettre_pret()
        self.assertEqual(self.deployer_b(), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-03", action="deployer-application", commit=self.commit_b,
                                        version="1.0056", go=GO), "réussi")
        etat = json.loads(lire(os.path.join(self.env.etat_dir, "application.json")))
        self.assertEqual(etat["precedent"]["commit"], self.env.commit_a)

    def test_adopter_avant_deployer(self):
        self.commit_b = self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self.commit_b,
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("adopter", self.env.resultat("2026-10-27-02"))
        self.assertEqual(self.env.appels(), [])


class TestEchecs(Base):
    def test_t4_build_en_echec_remet_les_fichiers_et_ne_fait_aucun_up(self):
        self.mettre_pret()
        self.env.docker(build_echec=True)
        self.assertEqual(self.deployer_b(), "échec, revenu")
        self.assertFalse([a for a in self.env.appels() if a[:1] == ["compose"] and a[7:] [:1] == ["up"]])
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")
        self.assertEqual(lire(os.path.join(self.env.app, "app/main.py")), "print('a')\n")
        self.assertTrue(os.path.exists(os.path.join(self.env.app, "app/ancien.py")))
        self.assertFalse(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertTrue(os.stat(os.path.join(self.env.app, "scripts/start.sh")).st_mode & 0o100)
        self.assertEqual(self.env.servi()["version"], "1.0055")
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))
        self.assertIn("erreur de compilation", self.env.resultat("2026-10-27-02"))

    def test_t5_sante_en_echec_revision_inchangee_retour_automatique(self):
        self.mettre_pret()
        self.env.docker(up_version="9.9999")
        self.assertEqual(self.deployer_b(), "échec, revenu")
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")
        self.assertTrue(os.path.exists(os.path.join(self.env.app, "app/ancien.py")))
        self.assertFalse(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertEqual(self.env.docker_etat()["version"], "1.0055")           # l'ancienne version répond
        ups = [a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] == ["up"]]
        self.assertEqual(len(ups), 2)
        self.assertEqual(self.env.servi()["version"], "1.0055")
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))
        self.assertEqual(self.env.interdits(), [])

    def test_t5_traceback_dans_le_journal_compte_comme_un_echec(self):
        self.mettre_pret()
        self.env.docker(logs_apres_up=["Traceback (most recent call last):", "  boom"])
        self.assertEqual(self.deployer_b(), "échec, revenu")
        self.assertIn("Traceback", self.env.resultat("2026-10-27-02"))

    def test_t5_echec_de_la_ligne_d_echec_du_journal(self):
        self.mettre_pret()
        self.env.docker(logs_apres_up=["2026 Échec de la migration"])
        self.assertEqual(self.deployer_b(), "échec, revenu")

    def test_t5_up_en_echec_revision_inchangee_retour_automatique(self):
        self.mettre_pret()
        self.env.docker(up_echec_une_fois=True)       # le premier `up` échoue, le `up` du retour automatique réussit
        self.assertEqual(self.deployer_b(), "échec, revenu")
        ups = [a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] == ["up"]]
        self.assertEqual(len(ups), 2)

    def test_t6_sante_en_echec_revision_changee_aucun_retour_file_arretee(self):
        self.mettre_pret()
        self.env.docker(up_version="9.9999", apres={"revision": "0040"})
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        # aucun retour : un seul build, un seul up, fichiers de la nouvelle version laissés
        builds = [a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] == ["build"]]
        ups = [a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] == ["up"]]
        self.assertEqual((len(builds), len(ups)), (1, 1))
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0056\n")
        r = self.env.resultat("2026-10-27-02")
        self.assertRegex(r, r"monprojet_deploiement-0039_\d{8}-\d{6}\.dump")     # le compte rendu nomme la sauvegarde
        self.assertIn("monprojet_rev-0039_20261001-010101.dump", r)             # et la dernière avant migration
        self.assertTrue(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))
        # addendum 2 : le nouveau code reste en place, donc il est « servi » (comme à l'étape 10), l'ancien « précédent »
        self.verifier_nouveau_servi("0040")
        self.assertIn("est en place mais la file est arrêtée", r)
        self.assertIn(self.commit_b, r)
        self.assertNotIn("incertain", self.env.application())
        # l'ordre suivant est refusé, sauf etat et reprendre-file
        self.env.vider_appels()
        self.assertEqual(self.env.jouer("2026-10-27-03", action="deployer-application", commit=self.commit_b,
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("file arrêtée depuis l'ordre 2026-10-27-02", self.env.resultat("2026-10-27-03"))
        self.assertEqual(self.env.appels(), [])
        self.assertEqual(self.env.jouer("2026-10-27-04", action="etat"), "réussi")
        self.assertIn("ARRÊTÉE", self.env.resultat("2026-10-27-04"))
        self.assertEqual(self.env.jouer("2026-10-27-05", action="reprendre-file", file="deploiement", go=GO), "réussi")
        self.assertIn("2026-10-27-02", self.env.resultat("2026-10-27-05"))
        self.assertFalse(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))
        # rouverte : un ordre est de nouveau accepté
        self.assertEqual(self.env.jouer("2026-10-27-06", action="etat"), "réussi")

    def test_reprendre_une_file_non_arretee_est_refuse(self):
        self.assertEqual(self.env.jouer("2026-10-27-01", action="reprendre-file", file="deploiement", go=GO), "refusé")

    def test_t7_table_d_histoire_en_baisse_arrete_la_file(self):
        self.mettre_pret()
        self.env.docker(apres={"tables": {"membres": 9, "evenements": 20, "autre": 3, "alembic_version": 1}})
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        r = self.env.resultat("2026-10-27-02")
        self.assertIn("| **membres (histoire)** | **10** | **9** |", r)
        self.assertTrue(os.path.exists(os.path.join(self.env.etat_dir, "arret-deploiement.json")))
        self.verifier_nouveau_servi("0039")
        self.assertIn("est en place mais la file est arrêtée", r)
        self.assertNotIn("incertain", self.env.application())

    def test_t7_table_d_histoire_absente_apres_arrete_la_file(self):
        self.mettre_pret()
        self.env.docker(apres={"tables": {"evenements": 20, "autre": 3, "alembic_version": 1}})
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        self.verifier_nouveau_servi("0039")

    def test_addendum2_le_deploiement_suivant_retire_selon_le_manifeste_du_code_en_place(self):
        """Après un arrêt « nouveau code en place », le déploiement suivant part du bon manifeste."""
        self.mettre_pret()
        self.env.docker(up_version="9.9999", apres={"revision": "0040"})
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        self.assertTrue(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertEqual(self.env.jouer("2026-10-27-03", action="reprendre-file", file="deploiement", go=GO), "réussi")
        self.env.docker(up_version=None, apres={"revision": "0040"})
        commit_c = self.env.commit_app({"VERSION": "1.0057\n", "app/main.py": "print('c')\n"}, retirer=["app/nouveau.py"])
        self.env.docker(up_version="1.0057", apres={"revision": "0040"})
        self.assertEqual(self.env.jouer("2026-10-27-04", action="deployer-application", commit=commit_c, version="1.0057",
                                        go=GO), "réussi")
        # nouveau.py venait du commit B (en place) : il est retiré, ce qui n'arrive que si le manifeste servi était celui de B
        self.assertFalse(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertEqual(self.env.servi()["commit"], commit_c)
        self.assertEqual(self.env.application()["precedent"]["commit"], self.commit_b)

    def test_t7_table_d_histoire_absente_avant_refuse_sans_rien_faire(self):
        self.mettre_pret()
        self.env.docker(tables={"evenements": 20, "autre": 3, "alembic_version": 1})
        self.assertEqual(self.deployer_b(), "refusé")
        self.assertIn("membres", self.env.resultat("2026-10-27-02"))
        self.assertFalse([a for a in self.env.appels() if a[0] in ("run",) or a[:1] == ["compose"] and a[7:8] in (["build"], ["up"])])
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_comptes_apres_illisibles_arretent_la_file(self):
        self.mettre_pret()
        self.env.docker(lecture_echec_apres_up=True)       # la base devient illisible dès que `up` a eu lieu
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")

    def test_addendum2_arret_a_etat_incertain_pose_le_champ_et_bloque_revenir_jusqu_au_prochain_succes(self):
        self.mettre_pret()
        self.env.docker(lecture_echec_apres_up=True)
        self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        self.env.docker(lecture_echec_apres_up=False)
        r = self.env.resultat("2026-10-27-02")
        self.assertIn("état réel à constater par `etat`", r)
        inc = self.env.application()["incertain"]
        self.assertEqual(inc["ordre"], "2026-10-27-02")
        self.assertIn("comptes après impossibles", inc["raison"])
        self.assertTrue(inc["date"])
        self.assertEqual(self.env.jouer("2026-10-27-03", action="reprendre-file", file="deploiement", go=GO), "réussi")
        # `etat` le dit ; `revenir` est refusé et ne touche à rien
        self.assertEqual(self.env.jouer("2026-10-27-04", action="etat"), "réussi")
        self.assertIn("INCERTAIN", self.env.resultat("2026-10-27-04"))
        self.env.vider_appels()
        self.assertEqual(self.env.jouer("2026-10-27-05", action="revenir", cible="application", go=GO), "refusé")
        self.assertIn("incertain", self.env.resultat("2026-10-27-05"))
        self.assertFalse([a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] in (["build"], ["up"])])
        # le prochain succès efface le champ
        commit_c = self.env.commit_app({"VERSION": "1.0057\n", "app/main.py": "print('c')\n"})
        self.env.docker(up_version="1.0057")
        self.assertEqual(self.env.jouer("2026-10-27-06", action="deployer-application", commit=commit_c, version="1.0057",
                                        go=GO), "réussi")
        self.assertNotIn("incertain", self.env.application())

    def test_addendum2_chaque_arret_incertain_pose_le_champ(self):
        """Remise des fichiers impossible après un build en échec : état incertain."""
        self.mettre_pret()
        self.env.docker(build_echec=True)
        with mock.patch.object(application, "_remettre_fichiers", return_value=False):
            self.assertEqual(self.deployer_b(), "échec, file arrêtée")
        self.assertIn("remise des fichiers", self.env.application()["incertain"]["raison"])


class TestControles(Base):
    def verifier_refus_sans_geste(self, ident="2026-10-27-02"):
        self.mettre_pret()
        self.assertEqual(self.deployer_b(ident), "refusé")
        for a in self.env.appels():
            self.assertNotIn(a[0] if a[0] != "compose" else a[7], ("build", "up", "run"))
            self.assertNotEqual(a[:3], ["exec", "monprojet-db-1", "sh"])      # pas de dump
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")
        self.assertEqual(self.env.interdits(), [])
        return self.env.resultat(ident)

    def test_t8_projet_different(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        e["projet"] = "autreprojet"
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application",
                                        commit=self._tete(), version="1.0056", go=GO), "refusé")
        self.assertEqual([a for a in self.env.appels() if a[:1] != ["compose"] or a[7:8] != ["ps"]], [])

    def _tete(self):
        from outils import git
        return git("rev-parse", "HEAD", cwd=self.env.src).strip()

    def test_t8_etiquette_de_projet_du_conteneur_differente(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        e["etiquettes_db"]["com.docker.compose.project"] = "autre"
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("autre", self.env.resultat("2026-10-27-02"))
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_t8_dossier_different(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        e["etiquettes_db"]["com.docker.compose.project.working_dir"] = "/ailleurs"
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("/ailleurs", self.env.resultat("2026-10-27-02"))

    def test_t8_volume_sans_l_etiquette_du_projet(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        e["volumes"]["monprojet_images"] = {}
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("monprojet_images", self.env.resultat("2026-10-27-02"))

    def test_t8_volume_manquant(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        del e["volumes"]["monprojet_bruts"]
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")

    def test_t8_montage_de_la_base_different(self):
        self.mettre_pret()
        e = self.env.docker_etat()
        e["montages"][0]["Name"] = "un_autre_volume"
        self.env.docker_ecrire(e)
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("monte pas", self.env.resultat("2026-10-27-02"))

    def test_t8_service_db_absent(self):
        self.mettre_pret()
        self.env.docker(services={"app": "running"})
        self.env.nouveau_commit_b()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "refusé")

    def test_t8_etat_le_constate_et_le_dit(self):
        e = self.env.docker_etat()
        e["etiquettes_db"]["com.docker.compose.project"] = "autre"
        self.env.docker_ecrire(e)
        self.assertEqual(self.env.jouer("2026-10-27-01", action="etat"), "réussi")
        r = self.env.resultat("2026-10-27-01")
        self.assertIn("contrôle du projet en échec", r)
        self.assertIn("non lue", r)       # la base n'est pas interrogée dans le mauvais projet
        self.assertFalse([a for a in self.env.appels() if a[0] == "exec"])

    def test_t9_dump_vide(self):
        self.mettre_pret()
        self.env.docker(dump="vide")
        self.assertEqual(self.deployer_b(), "refusé")
        self.assertTrue(any(n.endswith(".dump.part.echec") for n in self.env.sauvegardes()), self.env.sauvegardes())
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")
        self.assertFalse([a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] in (["build"], ["up"])])
        self.assertFalse(any(n.endswith(".dump") and "deploiement" in n for n in self.env.sauvegardes()))

    def test_t9_liste_du_dump_en_echec(self):
        self.mettre_pret()
        self.env.docker(restore_list="echec")
        self.assertEqual(self.deployer_b(), "refusé")
        self.assertTrue(any(".echec" in n for n in self.env.sauvegardes()))
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_t9_dump_avec_trop_peu_d_entrees(self):
        self.mettre_pret()
        self.env.docker(restore_list="peu")
        self.assertEqual(self.deployer_b(), "refusé")
        self.assertIn("TABLE DATA", self.env.resultat("2026-10-27-02"))
        self.assertTrue(any(".echec" in n for n in self.env.sauvegardes()))

    def test_t9_archive_des_ecussons_illisible(self):
        self.mettre_pret()
        self.env.docker(tar="illisible")
        self.assertEqual(self.deployer_b(), "refusé")
        echecs = [n for n in self.env.sauvegardes() if ".echec" in n]
        self.assertEqual(len(echecs), 2)           # le dump aussi est gardé en .echec
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_t9_archive_des_ecussons_vide(self):
        self.mettre_pret()
        self.env.docker(tar="vide")
        self.assertEqual(self.deployer_b(), "refusé")

    def test_t10_archive_avec_env_ou_backups_refusee(self):
        self.mettre_pret()
        for nom in (".env", "backups/x.dump"):
            commit = self.env.commit_app({"VERSION": "1.0056\n", nom: "x"})
            ident = "2026-10-27-%02d" % (10 + len(nom))
            self.assertEqual(self.env.jouer(ident, action="deployer-application", commit=commit, version="1.0056",
                                            go=GO), "refusé", nom)
            self.assertIn("protégés", self.env.resultat(ident))
            self.env.commit_app({}, retirer=[nom])
        self.assertEqual(lire(os.path.join(self.env.app, ".env")), "SECRET=abc\n")
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_t10_chemin_ajoute_par_la_configuration_refuse(self):
        self.mettre_pret()
        self.env.dict_config["application"]["chemins_proteges"] = [".env.SAVE"]
        commit = self.env.commit_app({"VERSION": "1.0056\n", ".env.SAVE": "x"})
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=commit, version="1.0056",
                                        go=GO), "refusé")
        self.assertIn("protégés", self.env.resultat("2026-10-27-02"))
        self.assertIn(".env.SAVE", self.env.resultat("2026-10-27-02"))
        self.assertEqual(lire(os.path.join(self.env.app, ".env.SAVE")), "SECRET=old\n")
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_t10_env_example_dans_l_archive_est_accepte_et_pose(self):
        """v0.1.1 : le modèle .env.example livré par l'application n'est plus un chemin protégé."""
        self.mettre_pret()
        commit = self.env.commit_app({"VERSION": "1.0056\n", ".env.example": "SECRET=\n"})
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=commit, version="1.0056",
                                        go=GO), "réussi")
        self.assertEqual(lire(os.path.join(self.env.app, ".env.example")), "SECRET=\n")
        self.assertEqual(lire(os.path.join(self.env.app, ".env")), "SECRET=abc\n")          # propre à la machine, intact
        self.assertEqual(lire(os.path.join(self.env.app, ".env.SAVE")), "SECRET=old\n")     # inconnu des manifestes, intact

    def test_t10_version_differente_de_l_ordre(self):
        self.mettre_pret()
        commit = self.env.nouveau_commit_b("1.0056")
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=commit,
                                        version="1.0099", go=GO), "refusé")
        self.assertIn("VERSION", self.env.resultat("2026-10-27-02"))
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")

    def test_commit_inconnu_refuse(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit="a" * 40,
                                        version="1.0056", go=GO), "refusé")
        self.assertIn("n'existe pas", self.env.resultat("2026-10-27-02"))

    def test_place_insuffisante_refuse(self):
        self.mettre_pret()
        self.env.dict_config["application"]["place_min_deploiement_go"] = 10 ** 9
        commit = self.env.nouveau_commit_b()
        self.env.ordre("2026-10-27-02", action="deployer-application", commit=commit, version="1.0056", go=GO)
        self.env.lancer()
        self.assertEqual(self.env.statut("2026-10-27-02"), "refusé")
        self.assertIn("place insuffisante", self.env.resultat("2026-10-27-02"))


class TestRevenir(Base):
    def test_t12_revenir_accepte_sans_migration(self):
        self.mettre_pret()
        self.assertEqual(self.deployer_b(), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-03", action="revenir", cible="application", go=GO), "réussi")
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")
        self.assertTrue(os.path.exists(os.path.join(self.env.app, "app/ancien.py")))
        self.assertFalse(os.path.exists(os.path.join(self.env.app, "app/nouveau.py")))
        self.assertEqual(self.env.servi()["version"], "1.0055")
        self.assertEqual(self.env.docker_etat()["version"], "1.0055")

    def test_t12_revenir_refuse_quand_la_revision_a_change(self):
        self.mettre_pret()
        self.env.nouveau_commit_b()
        self.env.docker(apres={"revision": "0040"})
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self._tete(),
                                        version="1.0056", go=GO), "réussi")
        self.env.vider_appels()
        self.assertEqual(self.env.jouer("2026-10-27-03", action="revenir", cible="application", go=GO), "refusé")
        r = self.env.resultat("2026-10-27-03")
        self.assertIn("migration", r)
        self.assertIn("monprojet_deploiement-0039", r)         # la sauvegarde à utiliser est nommée
        self.assertFalse([a for a in self.env.appels() if a[:1] == ["compose"] and a[7:8] in (["build"], ["up"])])
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0056\n")

    def _tete(self):
        from outils import git
        return git("rev-parse", "HEAD", cwd=self.env.src).strip()

    def test_t12_revenir_sans_precedent(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="revenir", cible="application", go=GO), "refusé")

    def test_t12_essai_a_blanc_revenir_apres_un_redeploiement_identique(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-application", commit=self.env.commit_a,
                                        version="1.0055", go=GO), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-03", action="revenir", cible="application", go=GO), "réussi")
        self.assertEqual(lire(os.path.join(self.env.app, "VERSION")), "1.0055\n")


class TestPurge(Base):
    def test_t16_la_purge_garde_au_moins_trois_et_ne_touche_pas_aux_autres_familles(self):
        self.mettre_pret()
        d = os.path.join(self.env.app, "backups")
        for i in range(8):
            base = "monprojet_deploiement-0030_2026100%d-120000" % (i + 1)
            ecrire(os.path.join(d, base + ".dump"), "x")
            ecrire(os.path.join(d, base + "_ecussons.tar.gz"), "x")
        autres = ["monprojet_rev-0030_20260901-000000.dump", "monprojet_auto-20260901-000000.dump",
                  "monprojet_manuel-20260901-000000.dump", "monprojet_manuel-20260901-000000_ecussons.tar.gz",
                  "autre_deploiement-0001_20260101-000000.dump", "monprojet_deploiement-0030_20260101-000000.dump.echec"]
        for n in autres:
            ecrire(os.path.join(d, n), "x")
        self.env.dict_config["application"]["sauvegardes_garder"] = 1      # < 3 vaut 3
        self.assertEqual(self.deployer_b(), "réussi")
        restants = [n for n in os.listdir(d) if re.match(r"^monprojet_deploiement-.+_\d{8}-\d{6}\.dump$", n)]
        self.assertEqual(len(restants), 3, sorted(restants))
        for n in restants:
            self.assertTrue(os.path.exists(os.path.join(d, n.replace(".dump", "_ecussons.tar.gz"))))
        for n in autres + ["monprojet_rev-0039_20261001-010101.dump", "monprojet_auto-20261002-010101.dump"]:
            self.assertTrue(os.path.exists(os.path.join(d, n)), n)
        # la plus récente (celle de ce déploiement) est gardée
        self.assertTrue(any("0039" in n for n in restants))

    def test_t16_la_purge_garde_le_nombre_configure_au_dessus_de_trois(self):
        self.mettre_pret()
        d = os.path.join(self.env.app, "backups")
        for i in range(8):
            base = "monprojet_deploiement-0030_2026100%d-120000" % (i + 1)
            ecrire(os.path.join(d, base + ".dump"), "x")
            ecrire(os.path.join(d, base + "_ecussons.tar.gz"), "x")
        self.env.dict_config["application"]["sauvegardes_garder"] = 5
        self.assertEqual(self.deployer_b(), "réussi")
        restants = [n for n in os.listdir(d) if re.match(r"^monprojet_deploiement-.+_\d{8}-\d{6}\.dump$", n)]
        self.assertEqual(len(restants), 5)

    def test_t16_une_purge_n_a_pas_lieu_apres_un_echec(self):
        self.mettre_pret()
        d = os.path.join(self.env.app, "backups")
        for i in range(8):
            ecrire(os.path.join(d, "monprojet_deploiement-0030_2026100%d-120000.dump" % (i + 1)), "x")
        self.env.dict_config["application"]["sauvegardes_garder"] = 3
        self.env.docker(build_echec=True)
        self.assertEqual(self.deployer_b(), "échec, revenu")
        restants = [n for n in os.listdir(d) if re.match(r"^monprojet_deploiement-.+\.dump$", n)]
        self.assertEqual(len(restants), 9)


class TestOrdresJoues(Base):
    def test_t2_un_ordre_ne_se_joue_qu_une_fois(self):
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.lancer()
        self.assertEqual(self.env.statut("2026-10-27-01"), "réussi")
        n = len(self.env.appels())
        self.assertGreater(n, 0)
        self.env.lancer()
        self.env.lancer()
        self.assertEqual(len(self.env.appels()), n)

    def test_t2_les_ordres_se_jouent_par_ordre_d_id(self):
        self.env.ordre("2026-10-27-03", action="etat")
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.ordre("2026-10-27-02", action="etat")
        self.env.lancer()
        journal = json.loads(lire(os.path.join(self.env.etat_dir, "journal-deploiement.json")))["ordres"]
        debuts = sorted(journal, key=lambda k: journal[k]["debut"] + k)
        self.assertEqual(debuts, ["2026-10-27-01", "2026-10-27-02", "2026-10-27-03"])
        lignes = [l for l in self.env.sortie if "début" in l]
        self.assertEqual([re.search(r"ordre (\S+) :", l).group(1) for l in lignes],
                         ["2026-10-27-01", "2026-10-27-02", "2026-10-27-03"])

    def test_t2_un_ordre_en_cours_au_demarrage_passe_interrompu_sans_etre_rejoue(self):
        self.env.ordre("2026-10-27-01", action="etat")
        # un passage précédent coupé : l'ordre est « en cours » au journal
        self.env.lancer()          # crée l'état puis joue l'ordre ; on le remet « en cours »
        chemin = os.path.join(self.env.etat_dir, "journal-deploiement.json")
        j = json.loads(lire(chemin))
        j["ordres"]["2026-10-27-01"]["statut"] = "en cours"
        ecrire(chemin, json.dumps(j))
        self.env.vider_appels()
        self.env.lancer()
        self.assertEqual(self.env.statut("2026-10-27-01"), "interrompu")
        self.assertEqual(self.env.appels(), [])
        self.env.lancer()
        self.assertEqual(self.env.appels(), [])

    def test_t2_un_ordre_interrompu_n_arrete_pas_la_file(self):
        self.env.ordre("2026-10-27-01", action="etat")
        self.env.lancer()
        chemin = os.path.join(self.env.etat_dir, "journal-deploiement.json")
        j = json.loads(lire(chemin))
        j["ordres"]["2026-10-27-01"]["statut"] = "en cours"
        ecrire(chemin, json.dumps(j))
        self.assertEqual(self.env.jouer("2026-10-27-02", action="etat"), "réussi")

    def test_etat_rapporte_tout(self):
        self.mettre_pret()
        self.assertEqual(self.env.jouer("2026-10-27-02", action="etat"), "réussi")
        r = self.env.resultat("2026-10-27-02")
        for morceau in ("version servie (santé) : 1.0055", "commit servi selon le déployeur", "révision de migration : 0039",
                        "libres", "famille rev", "famille auto", "Suites", "Ordres joués", "en marche", "membres (histoire)"):
            self.assertIn(morceau, r)
        self.assertEqual(self.env.interdits(), [])

    def test_ordre_invalide_refuse_et_joue_une_fois(self):
        self.env.ordre_brut("2026-10-27-01", "{pas du json")
        self.env.lancer()
        self.assertEqual(self.env.statut("2026-10-27-01"), "refusé")
        self.assertEqual(self.env.appels(), [])


if __name__ == "__main__":
    unittest.main()
