"""T11 : deployer-suite et revenir d'une suite."""

import hashlib
import os
import unittest

from outils import Env, ecrire, lire

COMMIT = "c" * 40
URL = "https://raw.exemple.test/exemple/suites/%s/dist/suite_a.html" % COMMIT


def sha(octets):
    return hashlib.sha256(octets).hexdigest()


class TestSuites(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)
        self.servi = os.path.join(self.env.suites_dir, "suite_a.html")
        self.prec = os.path.join(self.env.suites_dir, "suite_a.prec.html")
        ecrire(self.servi, b"<html>ancien</html>")
        self.nouveau = b"<html>nouveau</html>"
        self.env.faux_reseau.ajouter(URL, self.nouveau)

    def deployer(self, ident, sha256=None, commit=COMMIT):
        return self.env.jouer(ident, action="deployer-suite", suite="suite-a", commit=commit,
                              sha256=sha256 or sha(self.nouveau))

    def test_t11_sha256_faux_refuse_et_servi_intact(self):
        self.assertEqual(self.deployer("2026-10-27-01", sha256=sha(b"autre chose")), "refusé")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")
        self.assertFalse(os.path.exists(self.prec))
        self.assertEqual(sorted(os.listdir(self.env.suites_dir)), ["suite_a.html"])      # pas de reste temporaire
        self.assertIn("sha256", self.env.resultat("2026-10-27-01"))

    def test_t11_reussi_prec_egal_ancien_servi_egal_nouveau(self):
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        self.assertEqual(lire(self.servi), "<html>nouveau</html>")
        self.assertEqual(lire(self.prec), "<html>ancien</html>")
        self.assertEqual(sorted(os.listdir(self.env.suites_dir)), ["suite_a.html", "suite_a.prec.html"])
        for f in (self.servi, self.prec):
            self.assertEqual(os.stat(f).st_mode & 0o777, 0o644)
        self.assertEqual(self.env.faux_reseau.demandes, [URL])
        self.assertEqual(self.env.appels(), [])        # aucun redémarrage, aucun Docker
        self.assertIn(sha(self.nouveau), self.env.resultat("2026-10-27-01"))

    def test_t11_l_ancien_prec_est_remplace(self):
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        deuxieme = b"<html>troisieme</html>"
        url2 = "https://raw.exemple.test/exemple/suites/%s/dist/suite_a.html" % ("d" * 40)
        self.env.faux_reseau.ajouter(url2, deuxieme)
        self.assertEqual(self.env.jouer("2026-10-27-02", action="deployer-suite", suite="suite-a", commit="d" * 40,
                                        sha256=sha(deuxieme)), "réussi")
        self.assertEqual(lire(self.prec), "<html>nouveau</html>")
        self.assertEqual(lire(self.servi), "<html>troisieme</html>")

    def test_t11_premiere_pose_sans_fichier_servi(self):
        os.remove(self.servi)
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        self.assertEqual(lire(self.servi), "<html>nouveau</html>")
        self.assertFalse(os.path.exists(self.prec))

    def test_t11_telechargement_en_echec_servi_intact(self):
        self.env.faux_reseau.contenus.clear()
        self.assertEqual(self.deployer("2026-10-27-01"), "refusé")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")

    def test_t11_revenir_d_une_suite(self):
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-02", action="revenir", cible="suite-a"), "réussi")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")
        self.assertEqual(lire(self.prec), "<html>nouveau</html>")        # l'ancien servi devient le précédent
        # et un second retour rétablit
        self.assertEqual(self.env.jouer("2026-10-27-03", action="revenir", cible="suite-a"), "réussi")
        self.assertEqual(lire(self.servi), "<html>nouveau</html>")
        self.assertEqual(self.env.appels(), [])

    def test_t11_revenir_sans_precedent_refuse(self):
        self.assertEqual(self.env.jouer("2026-10-27-01", action="revenir", cible="suite-a"), "refusé")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")

    def test_t11_revenir_accepte_un_go_facultatif(self):
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-02", action="revenir", cible="suite-a", go="ok"), "réussi")

    def test_suite_aller_retour_du_fichier_servi(self):
        """L'essai à blanc : deployer-suite du fichier servi, puis revenir."""
        servi = lire(self.servi).encode()
        self.env.faux_reseau.ajouter(URL, servi)
        self.assertEqual(self.env.jouer("2026-10-27-01", action="deployer-suite", suite="suite-a", commit=COMMIT,
                                        sha256=sha(servi)), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-02", action="revenir", cible="suite-a"), "réussi")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")

    def test_l_etat_donne_les_sha256_des_suites(self):
        self.assertEqual(self.deployer("2026-10-27-01"), "réussi")
        self.assertEqual(self.env.jouer("2026-10-27-02", action="etat"), "réussi")
        r = self.env.resultat("2026-10-27-02")
        self.assertIn(sha(self.nouveau), r)
        self.assertIn(sha(b"<html>ancien</html>"), r)

    def test_la_suite_est_refusee_sur_une_file_arretee(self):
        self.env.dict_config  # noqa: B018
        os.makedirs(self.env.etat_dir, exist_ok=True)
        ecrire(os.path.join(self.env.etat_dir, "arret-deploiement.json"),
               '{"ordre": "2026-10-26-01", "raison": "test", "date": "2026-10-26T00:00:00Z"}')
        self.assertEqual(self.deployer("2026-10-27-01"), "refusé")
        self.assertEqual(lire(self.servi), "<html>ancien</html>")


if __name__ == "__main__":
    unittest.main()
