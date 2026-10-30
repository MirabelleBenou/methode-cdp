"""T13 : les opérations de fichiers enfermées dans des zones."""

import hashlib
import io
import os
import tarfile
import unittest
import zipfile

from deployeur import config
from outils import Env, ecrire, lire

COMMIT = "e" * 40


def sha(octets):
    return hashlib.sha256(octets).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)
        self.z = self.env.zone_fichiers          # zone « fichiers » (imbriquée dans « donnees »)
        self.t = self.env.zone_donnees
        self.n = 0

    def jouer(self, *operations, go=None):
        self.n += 1
        ident = "2026-10-27-%02d" % self.n
        champs = {"action": "fichiers", "operations": list(operations)}
        if go:
            champs["go"] = go
        statut = self.env.jouer(ident, **champs)
        self.ident = ident
        self.rapport = self.env.resultat(ident)
        return statut

    def mode(self, chemin):
        return os.stat(chemin).st_mode & 0o7777

    def corbeille(self, *morceaux, ident=None):
        return os.path.join(self.z, "_corbeille", ident or self.ident, *morceaux)


class TestBasique(Base):
    def test_creer_lister_empreinte(self):
        ecrire(os.path.join(self.z, "a", "f.txt"), "bonjour")
        self.assertEqual(self.jouer(
            {"operation": "creer-dossier", "zone": "fichiers", "chemin": "x/y/z"},
            {"operation": "lister", "zone": "fichiers", "chemin": "", "profondeur": 2},
            {"operation": "empreinte", "zone": "fichiers", "chemins": ["a/f.txt"]}), "réussi")
        self.assertTrue(os.path.isdir(os.path.join(self.z, "x", "y", "z")))
        self.assertEqual(self.mode(os.path.join(self.z, "x", "y", "z")), 0o755)
        self.assertIn("a/f.txt", self.rapport)
        self.assertIn(sha(b"bonjour"), self.rapport)
        self.assertIn("place libre", self.rapport)

    def test_lister_au_plus_500_entrees(self):
        for i in range(520):
            ecrire(os.path.join(self.z, "d", "f%03d" % i), "x")
        self.assertEqual(self.jouer({"operation": "lister", "zone": "fichiers", "chemin": "d"}), "réussi")
        self.assertIn("tronquée à 500", self.rapport)
        self.assertEqual(self.rapport.count("fichier 1 o"), 500)

    def test_creer_dossier_existant_est_idempotent(self):
        os.makedirs(os.path.join(self.z, "a"))
        self.assertEqual(self.jouer({"operation": "creer-dossier", "zone": "fichiers", "chemin": "a"}), "réussi")

    def test_la_premiere_operation_en_erreur_arrete_l_ordre(self):
        self.assertEqual(self.jouer(
            {"operation": "creer-dossier", "zone": "fichiers", "chemin": "un"},
            {"operation": "lister", "zone": "fichiers", "chemin": "inexistant"},
            {"operation": "creer-dossier", "zone": "fichiers", "chemin": "deux"}), "refusé")
        self.assertTrue(os.path.isdir(os.path.join(self.z, "un")))
        self.assertFalse(os.path.exists(os.path.join(self.z, "deux")))
        self.assertIn("2. lister", self.rapport)
        self.assertIn("1 opération(s) faite(s) avant l'arrêt sur 3", self.rapport)


class TestChemins(Base):
    def refus_sans_effet(self, *ops):
        avant = sorted(os.listdir(self.z))
        self.assertEqual(self.jouer(*ops), "refusé")
        self.assertEqual(sorted(os.listdir(self.z)), avant)
        return self.rapport

    def test_t13_point_point_refuse(self):
        r = self.refus_sans_effet({"operation": "creer-dossier", "zone": "fichiers", "chemin": "../evade"})
        self.assertIn("..", r)
        self.assertFalse(os.path.exists(os.path.join(self.t, "evade")))
        self.refus_sans_effet({"operation": "creer-dossier", "zone": "fichiers", "chemin": "a/../../evade"})

    def test_t13_chemin_absolu_refuse(self):
        self.refus_sans_effet({"operation": "creer-dossier", "zone": "fichiers", "chemin": "/tmp/evade-absolu"})
        self.assertFalse(os.path.exists("/tmp/evade-absolu"))
        self.refus_sans_effet({"operation": "lister", "zone": "fichiers", "chemin": "/etc"})

    def test_t13_octet_nul_refuse(self):
        self.refus_sans_effet({"operation": "creer-dossier", "zone": "fichiers", "chemin": "a\u0000b"})

    def test_t13_lien_symbolique_qui_sort_de_la_zone_refuse(self):
        self.env.dict_config["depots_publics"] = ["exemple/depot"]
        dehors = os.path.join(self.env.racine, "dehors")
        os.makedirs(dehors)
        ecrire(os.path.join(dehors, "secret.txt"), "secret")
        os.symlink(dehors, os.path.join(self.z, "lien"))
        os.symlink(os.path.join(dehors, "secret.txt"), os.path.join(self.z, "lienfichier"))
        for op in (
            {"operation": "lister", "zone": "fichiers", "chemin": "lien"},
            {"operation": "lister", "zone": "fichiers", "chemin": "lien/"},
            {"operation": "empreinte", "zone": "fichiers", "chemins": ["lien/secret.txt"]},
            {"operation": "empreinte", "zone": "fichiers", "chemins": ["lienfichier"]},
            {"operation": "creer-dossier", "zone": "fichiers", "chemin": "lien/nouveau"},
            {"operation": "copier", "zone": "fichiers", "de": "lien/secret.txt", "vers": "copie"},
            {"operation": "copier", "zone": "fichiers", "de": "lienfichier", "vers": "copie"},
            {"operation": "deplacer", "zone": "fichiers", "de": "lien", "vers": "ailleurs"},
            {"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "lienfichier"},
            {"operation": "telecharger", "zone": "fichiers", "chemin": "lien/x.bin",
             "source": "github:exemple/depot@%s:a.bin" % COMMIT},
        ):
            self.assertEqual(self.jouer(op), "refusé", op)
            self.assertIn("sort de la zone", self.rapport, op)
        self.assertTrue(os.path.exists(os.path.join(dehors, "secret.txt")))
        self.assertFalse(os.path.exists(os.path.join(dehors, "nouveau")))
        self.assertEqual(os.listdir(dehors), ["secret.txt"])

    def test_t13_lien_qui_reste_dans_la_zone_est_permis_pour_lire(self):
        ecrire(os.path.join(self.z, "reel", "f.txt"), "x")
        os.symlink(os.path.join(self.z, "reel"), os.path.join(self.z, "alias"))
        self.assertEqual(self.jouer({"operation": "lister", "zone": "fichiers", "chemin": "alias"}), "réussi")

    def test_t13_zone_inconnue_refusee(self):
        self.refus_sans_effet({"operation": "lister", "zone": "etc", "chemin": ""})

    def test_chemin_vide_refuse_pour_les_operations_qui_ecrivent(self):
        self.refus_sans_effet({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": ""})
        self.refus_sans_effet({"operation": "creer-dossier", "zone": "fichiers", "chemin": "."})

    def test_zones_imbriquees_chaque_chemin_se_controle_contre_sa_zone(self):
        ecrire(os.path.join(self.z, "f.txt"), "x")
        self.assertEqual(self.jouer({"operation": "empreinte", "zone": "donnees", "chemins": ["fichiers/f.txt"]}), "réussi")
        self.assertEqual(self.jouer({"operation": "empreinte", "zone": "fichiers", "chemins": ["../f.txt"]}), "refusé")


class TestZonesConfiguration(unittest.TestCase):
    def setUp(self):
        self.env = Env(self)

    def charger(self, chemin):
        d = self.env.dict_config
        d["zones"] = dict(d["zones"], interdite={"chemin": chemin, "place_min_go": 1})
        return config.valider(d)

    def test_t13_zones_interdites_refusees_au_chargement(self):
        interdites = [
            "/", "/home", "/home/quelquun/donnees", "/root", "/root/x", "/usr", "/usr/local/x", "/boot", "/boot/efi",
            "/etc", "/etc/x", "/etc/deployeur", "/var/lib/docker", "/var/lib/docker/volumes", "/var/lib/deployeur",
            "/var/lib/deployeur/travail", "/var/lib", "/var",
            self.env.app, os.path.join(self.env.app, "backups"), os.path.dirname(self.env.app),
            self.env.suites_dir, os.path.join(self.env.suites_dir, "sous"), self.env.etat_dir,
        ]
        for chemin in interdites:
            with self.assertRaises(config.ErreurConfig, msg=chemin) as cm:
                self.charger(chemin)
            self.assertIn("interdite", " ".join(cm.exception.problemes), chemin)

    def test_zone_relative_ou_avec_point_point_refusee(self):
        for chemin in ("relatif/zone", "/srv/../etc", ""):
            with self.assertRaises(config.ErreurConfig, msg=chemin):
                self.charger(chemin)

    def test_zone_qui_traverse_un_lien_vers_un_dossier_interdit_refusee(self):
        lien = os.path.join(self.env.racine, "lienversetc")
        os.symlink("/etc", lien)
        with self.assertRaises(config.ErreurConfig):
            self.charger(lien)

    def test_zone_conforme_acceptee(self):
        cfg = self.charger(os.path.join(self.env.racine, "autre_zone"))
        self.assertIn("interdite", cfg.zones)
        # deux zones imbriquées sont permises
        self.assertIn("donnees", cfg.zones)
        self.assertIn("fichiers", cfg.zones)

    def test_zone_de_transfert_inconnue_refusee(self):
        self.env.dict_config["zone_transfert"] = "nulle-part"
        with self.assertRaises(config.ErreurConfig):
            config.valider(self.env.dict_config)


class TestTelecharger(Base):
    def source(self, chemin="a.bin"):
        return "github:exemple/depot@%s:%s" % (COMMIT, chemin)

    def url(self, chemin="a.bin"):
        return "https://raw.exemple.test/exemple/depot/%s/%s" % (COMMIT, chemin)

    def setUp(self):
        super().setUp()
        self.env.dict_config["depots_publics"] = ["exemple/depot"]

    def test_depot_public_avec_sha256(self):
        self.env.faux_reseau.ajouter(self.url(), b"contenu")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "dl/a.bin",
                                     "source": self.source(), "sha256": sha(b"contenu")}), "réussi")
        self.assertEqual(lire(os.path.join(self.z, "dl", "a.bin")), "contenu")
        self.assertEqual(self.mode(os.path.join(self.z, "dl", "a.bin")), 0o644)
        self.assertEqual(os.listdir(os.path.join(self.z, "dl")), ["a.bin"])        # pas de .part

    def test_sha256_faux_refuse_sans_rien_laisser(self):
        self.env.faux_reseau.ajouter(self.url(), b"contenu")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "dl/a.bin",
                                     "source": self.source(), "sha256": sha(b"autre")}), "refusé")
        self.assertEqual(os.listdir(os.path.join(self.z, "dl")), [])

    def test_cible_existante_refusee(self):
        ecrire(os.path.join(self.z, "a.bin"), "ancien")
        self.env.faux_reseau.ajouter(self.url(), b"contenu")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": self.source()}), "refusé")
        self.assertEqual(lire(os.path.join(self.z, "a.bin")), "ancien")

    def test_depot_hors_liste_refuse(self):
        for source in ("github:autre/depot@%s:a.bin" % COMMIT,
                       "https://github.com/autre/depot/releases/download/v1/a.bin",
                       "https://hote-inconnu.test/a.bin", "http://cdn.exemple.test/a.bin",
                       "ftp://cdn.exemple.test/a.bin", "https://cdn.exemple.test:8443/a.bin",
                       "https://user:pw@cdn.exemple.test/a.bin", "github:exemple/depot@court:a.bin",
                       "github:exemple/depot@%s:../a.bin" % COMMIT, "https://github.com/exemple/depot/blob/main/a"):
            self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "x.bin",
                                         "source": source}), "refusé", source)
        self.assertEqual(self.env.faux_reseau.demandes, [])

    def test_hote_autorise(self):
        self.env.faux_reseau.ajouter("https://cdn.exemple.test/dir/f.zip", b"zip?")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "f.zip",
                                     "source": "https://cdn.exemple.test/dir/f.zip"}), "réussi")

    def test_release_d_un_depot_public_et_ses_redirections(self):
        release = "https://github.com/exemple/depot/releases/download/v1/a.bin"
        self.env.faux_reseau.redirection(release, "https://objects.githubusercontent.com/xyz/a.bin?sig=1")
        self.env.faux_reseau.ajouter("https://objects.githubusercontent.com/xyz/a.bin?sig=1", b"release")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": release}), "réussi")
        self.assertEqual(lire(os.path.join(self.z, "a.bin")), "release")

    def test_redirection_vers_un_hote_non_permis_refusee(self):
        self.env.faux_reseau.redirection(self.url(), "https://pirate.test/a.bin")
        self.env.faux_reseau.ajouter("https://pirate.test/a.bin", b"mauvais")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": self.source()}), "refusé")
        self.assertFalse(os.path.exists(os.path.join(self.z, "a.bin")))
        self.assertNotIn("https://pirate.test/a.bin", self.env.faux_reseau.demandes)

    def test_redirection_vers_http_refusee(self):
        self.env.faux_reseau.redirection(self.url(), "http://raw.exemple.test/a.bin")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": self.source()}), "refusé")

    def test_objects_githubusercontent_refuse_hors_release(self):
        self.env.faux_reseau.redirection(self.url(), "https://objects.githubusercontent.com/xyz/a.bin")
        self.env.faux_reseau.ajouter("https://objects.githubusercontent.com/xyz/a.bin", b"x")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": self.source()}), "refusé")

    def test_aucun_bit_d_execution(self):
        self.env.faux_reseau.ajouter(self.url("run.sh"), b"#!/bin/sh\nrm -rf /\n")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "run.sh",
                                     "source": self.source("run.sh")}), "réussi")
        self.assertEqual(self.mode(os.path.join(self.z, "run.sh")) & 0o111, 0)

    def test_place_insuffisante_refuse(self):
        self.env.dict_config["zones"]["fichiers"]["place_min_go"] = 10 ** 9
        self.env.faux_reseau.ajouter(self.url(), b"contenu")
        self.assertEqual(self.jouer({"operation": "telecharger", "zone": "fichiers", "chemin": "a.bin",
                                     "source": self.source()}), "refusé")
        self.assertIn("place insuffisante", self.rapport)
        self.assertEqual(self.env.faux_reseau.demandes, [])


class TestCopierDeplacer(Base):
    def test_copier_un_fichier_et_un_dossier_droits_normalises(self):
        ecrire(os.path.join(self.z, "src", "run.sh"), "#!/bin/sh\n", executable=True)
        ecrire(os.path.join(self.z, "src", "sub", "f.txt"), "f")
        self.assertEqual(self.jouer(
            {"operation": "copier", "zone": "fichiers", "de": "src", "vers": "copie/src2"},
            {"operation": "copier", "zone": "fichiers", "de": "src/sub/f.txt", "vers": "f2.txt"}), "réussi")
        self.assertEqual(lire(os.path.join(self.z, "copie", "src2", "sub", "f.txt")), "f")
        self.assertEqual(self.mode(os.path.join(self.z, "copie", "src2", "run.sh")), 0o644)
        self.assertEqual(self.mode(os.path.join(self.z, "copie", "src2")), 0o755)
        self.assertEqual(lire(os.path.join(self.z, "f2.txt")), "f")
        self.assertTrue(os.path.exists(os.path.join(self.z, "src", "run.sh")))      # la source reste
        self.assertEqual(sorted(os.listdir(self.z)), ["copie", "f2.txt", "src"])    # pas de reste temporaire

    def test_t13_cible_existante_sans_si_existe_refuse(self):
        ecrire(os.path.join(self.z, "a.txt"), "a")
        ecrire(os.path.join(self.z, "b.txt"), "b")
        for nom in ("copier", "deplacer"):
            self.assertEqual(self.jouer({"operation": nom, "zone": "fichiers", "de": "a.txt", "vers": "b.txt"}), "refusé")
            self.assertEqual(lire(os.path.join(self.z, "b.txt")), "b")
            self.assertEqual(lire(os.path.join(self.z, "a.txt")), "a")
            self.assertFalse(os.path.exists(os.path.join(self.z, "_corbeille")))

    def test_t13_avec_remplacer_l_ancienne_cible_va_a_la_corbeille(self):
        ecrire(os.path.join(self.z, "a.txt"), "a")
        ecrire(os.path.join(self.z, "d", "b.txt"), "b")
        self.assertEqual(self.jouer({"operation": "copier", "zone": "fichiers", "de": "a.txt", "vers": "d/b.txt",
                                     "si_existe": "remplacer"}), "réussi")
        self.assertEqual(lire(os.path.join(self.z, "d", "b.txt")), "a")
        self.assertEqual(lire(self.corbeille("d", "b.txt")), "b")
        ident = self.ident
        self.assertEqual(self.jouer({"operation": "deplacer", "zone": "fichiers", "de": "a.txt", "vers": "d/b.txt",
                                     "si_existe": "remplacer"}), "réussi")
        self.assertFalse(os.path.exists(os.path.join(self.z, "a.txt")))
        self.assertEqual(lire(os.path.join(self.z, "d", "b.txt")), "a")
        self.assertEqual(lire(self.corbeille("d", "b.txt")), "a")        # l'ancienne copie « a » est maintenant au rebut
        self.assertEqual(lire(self.corbeille("d", "b.txt", ident=ident)), "b")

    def test_deplacer_entre_zones(self):
        ecrire(os.path.join(self.z, "a.txt"), "a")
        self.assertEqual(self.jouer({"operation": "deplacer", "zone": "fichiers", "zone_vers": "donnees",
                                     "de": "a.txt", "vers": "dest/a.txt"}), "réussi")
        self.assertEqual(lire(os.path.join(self.t, "dest", "a.txt")), "a")
        self.assertFalse(os.path.exists(os.path.join(self.z, "a.txt")))

    def test_copie_dans_la_source_ou_sur_elle_meme_refusee(self):
        ecrire(os.path.join(self.z, "d", "f"), "x")
        self.assertEqual(self.jouer({"operation": "copier", "zone": "fichiers", "de": "d", "vers": "d/sous"}), "refusé")
        self.assertEqual(self.jouer({"operation": "deplacer", "zone": "fichiers", "de": "d", "vers": "d"}), "refusé")

    def test_copie_d_un_arbre_avec_lien_refusee(self):
        ecrire(os.path.join(self.z, "d", "f"), "x")
        os.symlink("f", os.path.join(self.z, "d", "lien"))
        self.assertEqual(self.jouer({"operation": "copier", "zone": "fichiers", "de": "d", "vers": "d2"}), "refusé")
        self.assertFalse(os.path.exists(os.path.join(self.z, "d2")))

    def test_la_corbeille_n_est_pas_une_cible(self):
        ecrire(os.path.join(self.z, "a.txt"), "a")
        self.assertEqual(self.jouer({"operation": "copier", "zone": "fichiers", "de": "a.txt",
                                     "vers": "_corbeille/x"}), "refusé")
        self.assertEqual(self.jouer({"operation": "creer-dossier", "zone": "fichiers", "chemin": "_corbeille/y"}), "refusé")

    def test_sortir_de_la_corbeille_est_permis(self):
        ecrire(os.path.join(self.z, "a.txt"), "a")
        self.assertEqual(self.jouer({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "a.txt"}), "réussi")
        self.assertEqual(self.jouer({"operation": "deplacer", "zone": "fichiers", "de": "_corbeille/%s/a.txt" % self.ident,
                                     "vers": "restauré.txt"}), "réussi")
        self.assertEqual(lire(os.path.join(self.z, "restauré.txt")), "a")


class TestCorbeille(Base):
    def test_mettre_a_la_corbeille_ne_supprime_rien(self):
        ecrire(os.path.join(self.z, "d", "f.txt"), "contenu")
        self.assertEqual(self.jouer({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "d/f.txt"}), "réussi")
        self.assertFalse(os.path.exists(os.path.join(self.z, "d", "f.txt")))
        self.assertEqual(lire(self.corbeille("d", "f.txt")), "contenu")

    def test_deux_mises_a_la_corbeille_du_meme_chemin_dans_un_ordre_ne_s_ecrasent_pas(self):
        ecrire(os.path.join(self.z, "f.txt"), "1")
        ident = "2026-10-27-%02d" % (self.n + 1)
        self.assertEqual(self.jouer(
            {"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "f.txt"},
            {"operation": "copier", "zone": "fichiers", "de": "_corbeille/%s/f.txt" % ident, "vers": "f.txt"},
            {"operation": "creer-dossier", "zone": "fichiers", "chemin": "z"},
            {"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "f.txt"}), "réussi")
        self.assertEqual(lire(self.corbeille("f.txt")), "1")
        self.assertEqual(lire(self.corbeille("f.txt.2")), "1")

    def test_t13_vider_la_corbeille_sans_go_refuse(self):
        ecrire(os.path.join(self.z, "f.txt"), "1")
        self.jouer({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "f.txt"})
        ident = self.ident
        self.assertEqual(self.jouer({"operation": "vider-la-corbeille", "zone": "fichiers"}), "refusé")
        self.assertEqual(lire(self.corbeille("f.txt", ident=ident)), "1")
        self.assertEqual(self.jouer({"operation": "vider-la-corbeille", "zone": "fichiers"}, go="  "), "refusé")
        self.assertEqual(lire(self.corbeille("f.txt", ident=ident)), "1")

    def test_vider_la_corbeille_avec_go(self):
        ecrire(os.path.join(self.z, "f.txt"), "1")
        ecrire(os.path.join(self.z, "g.txt"), "2")
        self.jouer({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "f.txt"})
        premier = self.ident
        self.jouer({"operation": "mettre-a-la-corbeille", "zone": "fichiers", "chemin": "g.txt"})
        second = self.ident
        self.assertEqual(self.jouer({"operation": "vider-la-corbeille", "zone": "fichiers", "id_corbeille": premier},
                                    go="oui"), "réussi")
        self.assertFalse(os.path.exists(os.path.join(self.z, "_corbeille", premier)))
        self.assertTrue(os.path.exists(os.path.join(self.z, "_corbeille", second, "g.txt")))
        self.assertEqual(self.jouer({"operation": "vider-la-corbeille", "zone": "fichiers"}, go="oui"), "réussi")
        self.assertEqual(os.listdir(os.path.join(self.z, "_corbeille")), [])
        self.assertTrue(os.path.isdir(os.path.join(self.z, "_corbeille")))

    def test_vider_la_corbeille_ne_touche_pas_la_corbeille_de_l_autre_zone(self):
        ecrire(os.path.join(self.t, "t.txt"), "t")
        self.jouer({"operation": "mettre-a-la-corbeille", "zone": "donnees", "chemin": "t.txt"})
        ident = self.ident
        self.assertEqual(self.jouer({"operation": "vider-la-corbeille", "zone": "fichiers"}, go="oui"), "réussi")
        self.assertTrue(os.path.exists(os.path.join(self.t, "_corbeille", ident, "t.txt")))

    def test_basculer(self):
        ecrire(os.path.join(self.z, "prepare", "index.html"), "nouveau")
        ecrire(os.path.join(self.z, "servi", "index.html"), "ancien")
        self.assertEqual(self.jouer({"operation": "basculer", "zone": "fichiers", "prepare": "prepare", "servi": "servi"}),
                         "réussi")
        self.assertEqual(lire(os.path.join(self.z, "servi", "index.html")), "nouveau")
        self.assertFalse(os.path.exists(os.path.join(self.z, "prepare")))
        self.assertEqual(lire(self.corbeille("servi", "index.html")), "ancien")

    def test_basculer_sans_servi_en_place(self):
        ecrire(os.path.join(self.z, "prepare", "index.html"), "nouveau")
        self.assertEqual(self.jouer({"operation": "basculer", "zone": "fichiers", "prepare": "prepare", "servi": "servi"}),
                         "réussi")
        self.assertEqual(lire(os.path.join(self.z, "servi", "index.html")), "nouveau")

    def test_basculer_sans_prepare_refuse(self):
        ecrire(os.path.join(self.z, "servi", "index.html"), "ancien")
        self.assertEqual(self.jouer({"operation": "basculer", "zone": "fichiers", "prepare": "prepare", "servi": "servi"}),
                         "refusé")
        self.assertEqual(lire(os.path.join(self.z, "servi", "index.html")), "ancien")


def tar_octets(membres, mode="w"):
    """membres : [(nom, type, donnees, options)] ; type 'f', 'd', 'l' (lien), 'h' (lien dur), 'p' (fifo), 'c' (périphérique)."""
    tampon = io.BytesIO()
    with tarfile.open(fileobj=tampon, mode=mode) as tf:
        for nom, typ, donnees, opts in membres:
            info = tarfile.TarInfo(nom)
            info.mode = opts.get("mode", 0o644)
            if typ == "f":
                info.size = len(donnees)
                tf.addfile(info, io.BytesIO(donnees))
            elif typ == "d":
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
            elif typ == "l":
                info.type = tarfile.SYMTYPE
                info.linkname = donnees
                tf.addfile(info)
            elif typ == "h":
                info.type = tarfile.LNKTYPE
                info.linkname = donnees
                tf.addfile(info)
            elif typ == "p":
                info.type = tarfile.FIFOTYPE
                tf.addfile(info)
            elif typ == "c":
                info.type = tarfile.CHRTYPE
                tf.addfile(info)
    return tampon.getvalue()


def tar_taille_annoncee(taille):
    info = tarfile.TarInfo("enorme.bin")
    info.size = taille
    return info.tobuf(tarfile.GNU_FORMAT)


class TestDecompresser(Base):
    def deposer(self, nom, octets):
        ecrire(os.path.join(self.z, nom), octets)

    def decompresser(self, archive="a.tar", vers="out"):
        return self.jouer({"operation": "decompresser", "zone": "fichiers", "archive": archive, "vers": vers})

    def test_tar_gz_zip_et_tgz_modes_normalises(self):
        membres = [("dossier", "d", b"", {"mode": 0o700}), ("dossier/run.sh", "f", b"#!/bin/sh", {"mode": 0o755}),
                   ("./autre.txt", "f", b"x", {})]
        self.deposer("a.tar", tar_octets(membres))
        self.deposer("b.tar.gz", tar_octets(membres, "w:gz"))
        self.deposer("c.tgz", tar_octets(membres, "w:gz"))
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w") as zf:
            zf.writestr("dossier/", b"")
            info = zipfile.ZipInfo("dossier/run.sh")
            info.external_attr = (0o100755) << 16
            zf.writestr(info, b"#!/bin/sh")
            zf.writestr("autre.txt", b"x")
        self.deposer("d.zip", tampon.getvalue())
        for i, (archive, sortie) in enumerate((("a.tar", "o1"), ("b.tar.gz", "o2"), ("c.tgz", "o3"), ("d.zip", "o4"))):
            self.assertEqual(self.decompresser(archive, sortie), "réussi", archive)
            base = os.path.join(self.z, sortie)
            self.assertEqual(lire(os.path.join(base, "dossier", "run.sh")), "#!/bin/sh")
            self.assertEqual(lire(os.path.join(base, "autre.txt")), "x")
            self.assertEqual(self.mode(os.path.join(base, "dossier", "run.sh")), 0o644)      # aucun bit d'exécution
            self.assertEqual(self.mode(os.path.join(base, "dossier")), 0o755)
            self.assertEqual(self.mode(os.path.join(base, "autre.txt")), 0o644)
        self.assertEqual(sorted(n for n in os.listdir(self.z) if n.startswith(".")), [])     # pas de reste temporaire

    def refuse_avant_extraction(self, nom_archive, octets, vers="out"):
        self.deposer(nom_archive, octets)
        avant = sorted(os.listdir(self.z))
        self.assertEqual(self.decompresser(nom_archive, vers), "refusé")
        self.assertEqual(sorted(os.listdir(self.z)), avant)           # rien créé, pas même un dossier temporaire
        return self.rapport

    def test_t13_archive_piegee_membre_absolu(self):
        self.refuse_avant_extraction("a.tar", tar_octets([("ok.txt", "f", b"1", {}), ("/tmp/evade-tar", "f", b"x", {})]))
        self.assertFalse(os.path.exists("/tmp/evade-tar"))

    def test_t13_archive_piegee_point_point(self):
        r = self.refuse_avant_extraction("a.tar", tar_octets([("ok.txt", "f", b"1", {}), ("../evade", "f", b"x", {})]))
        self.assertIn("..", r)
        self.refuse_avant_extraction("b.tar", tar_octets([("a/../../evade", "f", b"x", {})]))
        self.assertFalse(os.path.exists(os.path.join(self.t, "evade")))

    def test_t13_archive_piegee_lien_symbolique_et_lien_dur(self):
        r = self.refuse_avant_extraction("a.tar", tar_octets([("ok.txt", "f", b"1", {}), ("lien", "l", "/etc/passwd", {})]))
        self.assertIn("lien", r)
        self.refuse_avant_extraction("b.tar", tar_octets([("ok.txt", "f", b"1", {}), ("dur", "h", "ok.txt", {})]))

    def test_t13_archive_piegee_fichier_special(self):
        self.refuse_avant_extraction("a.tar", tar_octets([("fifo", "p", b"", {})]))
        self.refuse_avant_extraction("b.tar", tar_octets([("dev", "c", b"", {})]))

    def test_t13_archive_piegee_zip(self):
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w") as zf:
            zf.writestr("ok.txt", b"1")
            info = zipfile.ZipInfo("lien")
            info.external_attr = (0o120777) << 16
            zf.writestr(info, b"/etc/passwd")
        self.refuse_avant_extraction("a.zip", tampon.getvalue())
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w") as zf:
            zf.writestr("../evade", b"x")
        self.refuse_avant_extraction("b.zip", tampon.getvalue())
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w") as zf:
            zf.writestr("/abs", b"x")
        self.refuse_avant_extraction("c.zip", tampon.getvalue())

    def test_t13_archive_piegee_taille_annoncee_superieure_a_la_place(self):
        from unittest import mock
        from deployeur import fichiers
        self.deposer("a.tar", tar_octets([("gros.bin", "f", b"x" * (1 << 20), {})]))
        avant = sorted(os.listdir(self.z))
        with mock.patch.object(fichiers, "_libre", return_value=(1 << 20) + 1000):     # 1,1 Mio annoncé + 10 % > libre
            self.assertEqual(self.decompresser("a.tar"), "refusé")
        self.assertIn("place insuffisante", self.rapport)
        self.assertEqual(sorted(os.listdir(self.z)), avant)
        with mock.patch.object(fichiers, "_libre", return_value=(1 << 20) * 2):
            self.assertEqual(self.decompresser("a.tar"), "réussi")

    def test_t13_archive_piegee_en_tete_mensongere_refusee(self):
        enorme = tar_taille_annoncee(10 ** 12) + b"\0" * 1024
        self.refuse_avant_extraction("a.tar", enorme)

    def test_t13_place_minimale_de_la_zone_respectee_par_la_decompression(self):
        self.deposer("a.tar", tar_octets([("f", "f", b"x" * 1000, {})]))
        self.env.dict_config["zones"]["fichiers"]["place_min_go"] = 10 ** 9
        avant = sorted(os.listdir(self.z))
        self.assertEqual(self.decompresser("a.tar"), "refusé")
        self.assertEqual(sorted(os.listdir(self.z)), avant)

    def test_destination_existante_refusee(self):
        self.deposer("a.tar", tar_octets([("f", "f", b"x", {})]))
        os.makedirs(os.path.join(self.z, "out"))
        self.assertEqual(self.decompresser(), "refusé")
        self.assertEqual(os.listdir(os.path.join(self.z, "out")), [])

    def test_archive_illisible_refusee(self):
        self.refuse_avant_extraction("a.tar.gz", b"\x1f\x8bpas une archive")
        self.refuse_avant_extraction("b.zip", b"PK pas un zip")

    def test_extension_non_permise_refusee_a_la_validation(self):
        self.deposer("a.rar", b"x")
        self.assertEqual(self.decompresser("a.rar"), "refusé")


class TestPlaceEtPropriete(Base):
    def test_t13_place_minimale_pour_creer_un_dossier(self):
        self.env.dict_config["zones"]["fichiers"]["place_min_go"] = 10 ** 9
        self.assertEqual(self.jouer({"operation": "creer-dossier", "zone": "fichiers", "chemin": "x"}), "refusé")
        self.assertFalse(os.path.exists(os.path.join(self.z, "x")))
        # lecture seule : toujours permise
        self.assertEqual(self.jouer({"operation": "lister", "zone": "fichiers", "chemin": ""}), "réussi")

    def test_proprietaire_celui_de_la_racine_de_la_zone(self):
        st = os.stat(self.z)
        self.assertEqual(self.jouer({"operation": "creer-dossier", "zone": "fichiers", "chemin": "a/b"}), "réussi")
        for chemin in ("a", "a/b"):
            s = os.stat(os.path.join(self.z, chemin))
            self.assertEqual((s.st_uid, s.st_gid), (st.st_uid, st.st_gid))


class TestAucuneExecution(Base):
    def test_aucun_bit_d_execution_pose_nulle_part(self):
        ecrire(os.path.join(self.z, "s", "run.sh"), "#!/bin/sh", executable=True)
        self.env.faux_reseau.ajouter("https://raw.exemple.test/exemple/depot/%s/x.sh" % COMMIT, b"#!/bin/sh")
        self.env.dict_config["depots_publics"] = ["exemple/depot"]
        self.jouer({"operation": "copier", "zone": "fichiers", "de": "s", "vers": "s2"},
                   {"operation": "telecharger", "zone": "fichiers", "chemin": "x.sh",
                    "source": "github:exemple/depot@%s:x.sh" % COMMIT})
        for racine, dirs, fichiers in os.walk(self.z):
            for f in fichiers:
                chemin = os.path.join(racine, f)
                if "/s/" in chemin:
                    continue     # le fichier d'origine, posé par le test
                self.assertEqual(self.mode(chemin) & 0o111, 0, chemin)


if __name__ == "__main__":
    unittest.main()
