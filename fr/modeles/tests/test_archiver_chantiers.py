"""Tests de archiver_chantiers.py : dater, sortir, ne rien perdre, chercher ; les appels invalides.

Chaque test bâtit ses fixtures dans un dossier temporaire (voir outils_tests.py) et appelle le script en
ligne de commande avec « --date », pour que les jours se comptent sans dépendre de l'horloge.
"""
import re
import unittest
from collections import Counter

from .outils_tests import ARCHIVER, CasTemporaire, bloc, charger, yaml

JOUR = "2026-03-15"            # la date du jour des essais
IL_Y_A_7_JOURS = "2026-03-08"
IL_Y_A_6_JOURS = "2026-03-09"


def non_vides(texte: str) -> Counter:
    return Counter(ligne for ligne in texte.split("\n") if ligne.strip())


class CasArchiver(CasTemporaire):
    def setUp(self):
        super().setUp()
        self.dossier_archives = self.sous_dossier("archives")
        self.archive = self.dossier_archives / "CHANTIERS_2026-03.yaml"

    def ecrire_chantiers(self, *blocs: str, entete: str = "# Chantiers — Essai") -> str:
        self.chantiers = self.ecrire("chantiers.yaml", yaml(*blocs, entete=entete))
        return self.chantiers.read_text(encoding="utf-8")

    def lire_chantiers(self) -> str:
        return self.chantiers.read_bytes().decode("utf-8")

    def archiver(self, *options, date=JOUR):
        arguments = ["archiver", "--chantiers", self.chantiers, "--archives", self.dossier_archives]
        if date:
            arguments += ["--date", date]
        return self.lancer(ARCHIVER, *arguments, *options)

    def chercher(self, motif, *options):
        return self.lancer(ARCHIVER, "chercher", motif, "--chantiers", self.chantiers,
                           "--archives", self.dossier_archives, *options)


class TestDater(CasArchiver):
    def test_une_entree_en_recette_sans_date_est_datee_juste_apres_son_statut(self):
        self.ecrire_chantiers(bloc("alpha-1", titre="Premier", statut="recette", module="module-a"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire_chantiers(), yaml(
            "- id: alpha-1\n  titre: Premier\n  statut: recette\n  recette-le: 2026-03-15\n  module: module-a"))
        self.assertEqual(sortie.stdout, "archiver · 1 daté(s), 0 dédaté(s), 0 archivé(s)\n")
        self.assertFalse(self.archive.exists(), "une entrée datée au passage même ne sort pas")

    def test_les_autres_statuts_ne_sont_pas_dates(self):
        avant = self.ecrire_chantiers(*(bloc(f"alpha-{n}", statut=s) for n, s in
                                        enumerate(("a-venir", "a-cadrer", "en-vol", "dette"), start=1)))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0)
        self.assertEqual(self.lire_chantiers(), avant)
        self.assertEqual(sortie.stdout, "archiver · 0 daté(s), 0 dédaté(s), 0 archivé(s)\n")

    def test_dedater_une_entree_rouverte(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="en-vol", recette_le=IL_Y_A_6_JOURS, cdp="Opus-CdP-Alpha"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0)
        self.assertEqual(self.lire_chantiers(), yaml(bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha")))
        self.assertEqual(sortie.stdout, "archiver · 0 daté(s), 1 dédaté(s), 0 archivé(s)\n")

    def test_dater_et_dedater_dans_le_meme_passage(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette"),
                              bloc("alpha-2", statut="dette", recette_le=IL_Y_A_7_JOURS))
        sortie = self.archiver()
        self.assertEqual(sortie.stdout, "archiver · 1 daté(s), 1 dédaté(s), 0 archivé(s)\n")
        self.assertEqual(self.lire_chantiers(), yaml(bloc("alpha-1", statut="recette", recette_le=JOUR),
                                                     bloc("alpha-2", statut="dette")))

    def test_la_date_du_jour_par_defaut_est_celle_de_l_horloge(self):
        from datetime import date
        self.ecrire_chantiers(bloc("alpha-1", statut="recette"))
        sortie = self.archiver(date=None)
        self.assertEqual(sortie.code, 0)
        self.assertIn(f"  recette-le: {date.today().isoformat()}\n", self.lire_chantiers())

    def test_fin_de_ligne_windows_conservee(self):
        texte = "# Chantiers — Essai\r\n\r\n- id: alpha-1\r\n  statut: recette\r\n"
        self.chantiers = self.ecrire("chantiers.yaml", texte)
        self.archiver()
        self.assertEqual(self.lire_chantiers(),
                         "# Chantiers — Essai\r\n\r\n- id: alpha-1\r\n  statut: recette\r\n  recette-le: 2026-03-15\r\n")

    def test_fichier_sans_fin_de_ligne_finale_conserve(self):
        self.chantiers = self.ecrire("chantiers.yaml", "- id: alpha-1\n  statut: recette")
        self.archiver()
        self.assertEqual(self.lire_chantiers(), "- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-15")


class TestSortir(CasArchiver):
    def test_sept_jours_sort_six_jours_reste(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le=IL_Y_A_7_JOURS),
                              bloc("alpha-2", statut="recette", recette_le=IL_Y_A_6_JOURS))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire_chantiers(), yaml(bloc("alpha-2", statut="recette", recette_le=IL_Y_A_6_JOURS)))
        archive = self.archive.read_text(encoding="utf-8")
        self.assertIn("- id: alpha-1\n", archive)
        self.assertNotIn("alpha-2", archive)
        self.assertEqual(sortie.stdout.split("\n")[0],
                         f"archiver · 0 daté(s), 0 dédaté(s), 1 archivé(s) vers {self.archive}")
        self.assertEqual(sortie.stdout.split("\n")[1:], ["  alpha-1", ""])

    def test_le_delai_par_defaut_est_sept_jours(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-08"),
                              bloc("alpha-2", statut="recette", recette_le="2026-03-09"),
                              bloc("alpha-3", statut="recette", recette_le="2026-03-01"))
        self.archiver()
        restant = self.lire_chantiers()
        self.assertNotIn("alpha-1", restant)
        self.assertIn("alpha-2", restant)
        self.assertNotIn("alpha-3", restant)

    def test_l_archive_est_celle_du_mois_du_jour_avec_son_entete(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-20"))
        sortie = self.archiver(date="2026-04-02")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        archive = self.dossier_archives / "CHANTIERS_2026-04.yaml"
        self.assertTrue(archive.is_file())
        texte = archive.read_text(encoding="utf-8")
        self.assertTrue(texte.startswith("# Chantiers archivés — avril 2026\n"), texte)
        self.assertIn("au moins 7 jours", texte)
        self.assertTrue(texte.endswith("\n\n- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-20\n"), texte)
        self.assertEqual([p.name for p in self.dossier_archives.iterdir()], ["CHANTIERS_2026-04.yaml"])

    def test_le_nom_du_mois_dans_l_entete(self):
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
                "septembre", "octobre", "novembre", "décembre"]
        for numero, nom in enumerate(mois, start=1):
            with self.subTest(mois=nom):
                dossier = self.sous_dossier(f"archives-{numero}")
                self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2025-01-01"))
                self.lancer(ARCHIVER, "archiver", "--chantiers", self.chantiers, "--archives", dossier,
                            "--date", f"2026-{numero:02d}-10")
                texte = (dossier / f"CHANTIERS_2026-{numero:02d}.yaml").read_text(encoding="utf-8")
                self.assertTrue(texte.startswith(f"# Chantiers archivés — {nom} 2026\n"), texte)

    def test_delai_donne_par_l_option(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-12"),
                              bloc("alpha-2", statut="recette", recette_le="2026-03-13"))
        sortie = self.archiver("--delai", "3")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        restant = self.lire_chantiers()
        self.assertNotIn("alpha-1", restant)
        self.assertIn("alpha-2", restant)
        self.assertIn("au moins 3 jours", self.archive.read_text(encoding="utf-8"))

    def test_delai_plus_long_garde_une_entree_qui_sortirait_par_defaut(self):
        avant = self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"))
        sortie = self.archiver("--delai", "30")
        self.assertEqual(sortie.stdout, "archiver · 0 daté(s), 0 dédaté(s), 0 archivé(s)\n")
        self.assertEqual(self.lire_chantiers(), avant)
        self.assertFalse(self.archive.exists())

    def test_delai_zero_sort_une_entree_datee_du_jour_mais_pas_une_entree_datee_au_passage(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le=JOUR),
                              bloc("alpha-2", statut="recette"))
        sortie = self.archiver("--delai", "0")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire_chantiers(), yaml(bloc("alpha-2", statut="recette", recette_le=JOUR)))
        self.assertIn("- id: alpha-1\n", self.archive.read_text(encoding="utf-8"))
        self.assertEqual(sortie.stdout.split("\n")[0].split(" vers ")[0], "archiver · 1 daté(s), 0 dédaté(s), 1 archivé(s)")

    def test_seules_les_entrees_en_recette_sortent(self):
        avant = self.ecrire_chantiers(bloc("alpha-1", statut="dette", recette_le=IL_Y_A_7_JOURS))
        self.archiver()
        self.assertNotEqual(self.lire_chantiers(), avant, "la date d'une entrée non en recette est retirée")
        self.assertFalse(self.archive.exists())

    def test_plusieurs_entrees_sortent_dans_l_ordre_du_fichier(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"),
                              bloc("alpha-2", statut="a-venir"),
                              bloc("alpha-3", statut="recette", recette_le="2026-02-01"))
        sortie = self.archiver()
        self.assertEqual(sortie.stdout.split("\n")[1:], ["  alpha-1", "  alpha-3", ""])
        archive = self.archive.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^- id: (\S+)$", archive, flags=re.M), ["alpha-1", "alpha-3"])
        self.assertTrue(archive.endswith(
            "- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-01\n\n"
            "- id: alpha-3\n  statut: recette\n  recette-le: 2026-02-01\n"))

    def test_chaque_entree_sortie_se_retrouve_dans_l_archive_et_plus_dans_chantiers(self):
        ids = [f"alpha-{n}" for n in range(1, 6)]
        self.ecrire_chantiers(*(bloc(i, titre=f"Titre de {i}", statut="recette", recette_le="2026-03-01",
                                     module="module-a") for i in ids))
        self.archiver()
        archive = self.archive.read_text(encoding="utf-8")
        for i in ids:
            self.assertEqual(archive.count(f"- id: {i}\n"), 1, i)
            self.assertNotIn(i, self.lire_chantiers())

    def test_retrait_au_milieu_en_tete_et_en_fin_ne_laisse_jamais_deux_lignes_vides(self):
        ancien = bloc("ancien", statut="recette", recette_le="2026-03-01")
        a = bloc("alpha-1", statut="a-venir")
        b = bloc("alpha-2", statut="dette")
        for nom, blocs, reste in (("milieu", (a, ancien, b), (a, b)),
                                  ("en tête", (ancien, a, b), (a, b)),
                                  ("en fin", (a, b, ancien), (a, b)),
                                  ("seul", (ancien,), ())):
            with self.subTest(position=nom):
                self.ecrire_chantiers(*blocs)
                self.archiver()
                texte = self.lire_chantiers()
                self.assertNotIn("\n\n\n", texte)
                if reste:
                    self.assertEqual(texte, yaml(*reste))
                else:
                    self.assertNotIn("- id:", texte)
                self.archive.unlink()

    def test_commentaires_et_lignes_vides_entre_les_blocs_ne_sont_jamais_touches(self):
        texte = ("# Chantiers — Essai\n# libelle: module-a = Module Alpha\n\n"
                 "# --- lots livrés ---\n"
                 "- id: ancien\n  statut: recette\n  recette-le: 2026-03-01\n\n"
                 "# --- lots à venir ---\n"
                 "- id: alpha-1\n  statut: a-venir\n")
        self.chantiers = self.ecrire("chantiers.yaml", texte)
        self.archiver()
        self.assertEqual(self.lire_chantiers(), "# Chantiers — Essai\n# libelle: module-a = Module Alpha\n\n"
                                                "# --- lots livrés ---\n\n"
                                                "# --- lots à venir ---\n"
                                                "- id: alpha-1\n  statut: a-venir\n")

    def test_le_bloc_sort_tel_quel_avec_toutes_ses_cles(self):
        entree = bloc("alpha-1", titre="Un titre: avec deux-points", statut="recette", recette_le="2026-03-01",
                      module="module-a", mesure="a < b & c", version="v1.0.0")
        self.ecrire_chantiers(entree)
        self.archiver()
        self.assertTrue(self.archive.read_text(encoding="utf-8").endswith("\n\n" + entree + "\n"))


class TestARBlanc(CasArchiver):
    def test_a_blanc_n_ecrit_rien_et_dit_ce_qui_serait_fait(self):
        avant = self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"),
                                      bloc("alpha-2", statut="recette"),
                                      bloc("alpha-3", statut="dette", recette_le="2026-03-01"))
        sortie = self.archiver("--a-blanc")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(self.lire_chantiers(), avant)
        self.assertEqual(list(self.dossier_archives.iterdir()), [])
        self.assertEqual(sortie.stdout.split("\n")[0].split(" vers ")[0],
                         "archiver · 1 daté(s), 1 dédaté(s), 1 archivé(s)")
        self.assertIn("  alpha-1", sortie.stdout)

    def test_a_blanc_ne_touche_pas_une_archive_existante(self):
        existant = "# Archives\n\n" + bloc("alpha-0", statut="recette", recette_le="2026-02-01") + "\n"
        self.archive.write_text(existant, encoding="utf-8")
        avant = self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"))
        self.archiver("--a-blanc")
        self.assertEqual(self.archive.read_text(encoding="utf-8"), existant)
        self.assertEqual(self.lire_chantiers(), avant)

    def test_a_blanc_et_passage_reel_annoncent_la_meme_chose(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"),
                              bloc("alpha-2", statut="recette"))
        a_blanc = self.archiver("--a-blanc")
        reel = self.archiver()
        self.assertEqual(a_blanc.stdout, reel.stdout)


class TestIdempotence(CasArchiver):
    def test_un_second_passage_a_la_meme_date_ne_change_rien(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"),
                              bloc("alpha-2", statut="recette"),
                              bloc("alpha-3", statut="dette", recette_le="2026-03-01"),
                              bloc("alpha-4", statut="a-venir"))
        premier = self.archiver()
        self.assertEqual(premier.code, 0, premier.stdout + premier.stderr)
        chantiers, archive = self.chantiers.read_bytes(), self.archive.read_bytes()
        second = self.archiver()
        self.assertEqual(second.code, 0)
        self.assertEqual(second.stdout, "archiver · 0 daté(s), 0 dédaté(s), 0 archivé(s)\n")
        self.assertEqual(self.chantiers.read_bytes(), chantiers)
        self.assertEqual(self.archive.read_bytes(), archive)

    def test_rien_n_est_reecrit_quand_rien_ne_change(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="a-venir"))
        self.chantiers.chmod(0o644)
        avant = self.chantiers.stat().st_mtime_ns
        self.archiver()
        self.assertEqual(self.chantiers.stat().st_mtime_ns, avant)


class TestAucuneLignePerdue(CasArchiver):
    def test_chantiers_plus_archive_egalent_l_avant(self):
        avant = self.ecrire_chantiers(
            bloc("alpha-1", titre="Premier", statut="recette", recette_le="2026-03-01", module="module-a"),
            bloc("alpha-2", titre="Deuxième", statut="recette", module="module-a"),
            bloc("alpha-3", titre="Troisième", statut="en-vol", recette_le="2026-03-02", cdp="Opus-CdP-Alpha"),
            bloc("alpha-4", titre="Quatrième", statut="recette", recette_le=IL_Y_A_6_JOURS),
            bloc("alpha-5", titre="Cinquième", statut="recette", recette_le=IL_Y_A_7_JOURS, version="v1.0.0"),
            bloc("alpha-6", titre="Sixième", statut="a-cadrer"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        apres = self.lire_chantiers()
        ajout = self.archive.read_text(encoding="utf-8").split("\n\n", 1)[1]  # après l'en-tête
        attendu = non_vides(avant)
        attendu["  recette-le: 2026-03-15"] += 1      # alpha-2, daté au passage
        attendu["  recette-le: 2026-03-02"] -= 1      # alpha-3, rouvert, dédaté
        self.assertEqual(+attendu, non_vides(apres) + non_vides(ajout))

    def test_aucune_ligne_perdue_avec_des_commentaires_et_des_lignes_vides_en_tete_et_en_fin(self):
        avant = ("\n# Chantiers — Essai\n\n\n# note\n"
                 "- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-01\n"
                 "# note entre deux blocs\n\n\n"
                 "- id: alpha-2\n  statut: dette\n\n\n")
        self.chantiers = self.ecrire("chantiers.yaml", avant)
        self.archiver()
        ajout = self.archive.read_text(encoding="utf-8").split("\n\n", 1)[1]
        self.assertEqual(non_vides(avant), non_vides(self.lire_chantiers()) + non_vides(ajout))


class TestArchiveDuMois(CasArchiver):
    def test_l_archive_existante_recoit_l_ajout_sans_etre_reecrite(self):
        existant = "# Archives\n\n" + bloc("alpha-0", statut="recette", recette_le="2026-03-01") + "\n"
        self.archive.write_text(existant, encoding="utf-8")
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-02"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        nouveau = bloc("alpha-1", statut="recette", recette_le="2026-03-02") + "\n"
        self.assertEqual(self.archive.read_text(encoding="utf-8"), existant + "\n" + nouveau)

    def test_l_archive_existante_sans_fin_de_ligne_recoit_quand_meme_une_ligne_vide(self):
        existant = "# Archives\n\n- id: alpha-0\n  statut: recette"
        self.archive.write_text(existant, encoding="utf-8")
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-02"))
        self.archiver()
        self.assertEqual(self.archive.read_text(encoding="utf-8"),
                         existant + "\n\n- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-02\n")

    def test_l_archive_deja_separee_par_une_ligne_vide_n_en_recoit_pas_une_de_plus(self):
        existant = "# Archives\n\n- id: alpha-0\n  statut: recette\n\n"
        self.archive.write_text(existant, encoding="utf-8")
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-02"))
        self.archiver()
        self.assertEqual(self.archive.read_text(encoding="utf-8"),
                         existant + "- id: alpha-1\n  statut: recette\n  recette-le: 2026-03-02\n")

    def test_deux_passages_successifs_s_accumulent_dans_la_meme_archive(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"))
        self.archiver(date="2026-03-10")
        self.ecrire_chantiers(bloc("alpha-2", statut="recette", recette_le="2026-03-02"))
        self.archiver(date="2026-03-20")
        archive = self.archive.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^- id: (\S+)$", archive, flags=re.M), ["alpha-1", "alpha-2"])
        self.assertEqual(archive.count("# Chantiers archivés"), 1, "l'en-tête n'est écrit qu'à la création")

    def test_les_archives_d_un_autre_mois_ne_sont_pas_touchees(self):
        autre = self.dossier_archives / "CHANTIERS_2026-02.yaml"
        autre.write_text("# Février\n\n- id: alpha-0\n  statut: recette\n", encoding="utf-8")
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="2026-03-01"))
        self.archiver()
        self.assertEqual(autre.read_text(encoding="utf-8"), "# Février\n\n- id: alpha-0\n  statut: recette\n")


class TestDateIllisible(CasArchiver):
    def test_une_date_illisible_donne_le_code_1_un_avertissement_et_laisse_l_entree(self):
        avant = self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="pas-une-date"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 1)
        self.assertIn("id alpha-1 : recette-le illisible « pas-une-date »", sortie.stdout)
        self.assertEqual(self.lire_chantiers(), avant)
        self.assertFalse(self.archive.exists())

    def test_les_formes_de_date_refusees(self):
        for valeur in ("15/03/2026", "2026-02-30", "2026-13-01", "2026-3-1", "", "2026-03-01x"):
            with self.subTest(valeur=valeur):
                avant = self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le=valeur))
                sortie = self.archiver()
                self.assertEqual(sortie.code, 1, sortie.stdout)
                self.assertIn(f"recette-le illisible « {valeur} »", sortie.stdout)
                self.assertEqual(self.lire_chantiers(), avant)

    def test_les_autres_entrees_sont_traitees_malgre_l_avertissement(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="recette", recette_le="pas-une-date"),
                              bloc("alpha-2", statut="recette", recette_le="2026-03-01"),
                              bloc("alpha-3", statut="recette"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 1)
        restant = self.lire_chantiers()
        self.assertIn("alpha-1", restant)
        self.assertNotIn("alpha-2", restant)
        self.assertIn("recette-le: 2026-03-15", restant)
        self.assertIn("- id: alpha-2\n", self.archive.read_text(encoding="utf-8"))

    def test_une_entree_non_recette_avec_une_date_illisible_est_simplement_dedatee(self):
        self.ecrire_chantiers(bloc("alpha-1", statut="dette", recette_le="pas-une-date"))
        sortie = self.archiver()
        self.assertEqual(sortie.code, 0)
        self.assertEqual(self.lire_chantiers(), yaml(bloc("alpha-1", statut="dette")))


class TestChercher(CasArchiver):
    def setUp(self):
        super().setUp()
        self.ecrire_chantiers(bloc("alpha-1", titre="Premier lot", statut="a-venir", module="module-a"),
                              bloc("alpha-2", titre="Deuxième lot", statut="dette", module="module-b"))
        self.archive.write_text(
            "# Archives\n\n" + bloc("beta-1", titre="Ancien chantier", statut="recette", recette_le="2026-03-01") + "\n",
            encoding="utf-8")

    def test_un_id_vivant_donne_ce_seul_chantier_et_son_bloc(self):
        sortie = self.chercher("alpha-1")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        lignes = sortie.stdout.split("\n")
        self.assertEqual(lignes[0], f"{self.chantiers}:3 · alpha-1 · a-venir · Premier lot")
        self.assertEqual(lignes[1:-2], ["- id: alpha-1", "  titre: Premier lot", "  statut: a-venir", "  module: module-a"])
        self.assertEqual(lignes[-2], "chercher · 1 trouvé(s)")

    def test_un_id_archive_est_trouve_dans_l_archive(self):
        sortie = self.chercher("beta-1")
        self.assertEqual(sortie.code, 0)
        self.assertTrue(sortie.stdout.startswith(f"{self.archive}:3 · beta-1 · recette · Ancien chantier\n"), sortie.stdout)
        self.assertIn("  recette-le: 2026-03-01", sortie.stdout)
        self.assertIn("chercher · 1 trouvé(s)", sortie.stdout)

    def test_un_motif_cherche_sans_casse_dans_l_id_et_le_titre(self):
        sortie = self.chercher("ANCIEN")
        self.assertEqual(sortie.code, 0)
        self.assertIn("beta-1 · recette · Ancien chantier", sortie.stdout)
        sortie = self.chercher("deuxième")
        self.assertIn("alpha-2 · dette · Deuxième lot", sortie.stdout)

    def test_plusieurs_resultats_une_ligne_chacun_sans_bloc(self):
        sortie = self.chercher("lot")
        self.assertEqual(sortie.code, 0)
        self.assertEqual(len(sortie.stdout.strip().split("\n")), 3, "deux lignes d'entrée et le total")
        self.assertNotIn("- id:", sortie.stdout)
        self.assertTrue(sortie.stdout.endswith("chercher · 2 trouvé(s)\n"))

    def test_resultats_dans_l_ordre_chantiers_puis_archives(self):
        self.ecrire_chantiers(bloc("alpha-1", titre="Un lot", statut="a-venir"))
        (self.dossier_archives / "CHANTIERS_2026-02.yaml").write_text(
            "# A\n\n- id: zeta-1\n  titre: Un lot ancien\n  statut: recette\n", encoding="utf-8")
        sortie = self.chercher("lot")
        ids = re.findall(r" · (\S+) · ", sortie.stdout)
        self.assertEqual(ids, ["alpha-1", "zeta-1"])

    def test_un_motif_egal_a_un_id_donne_ce_seul_chantier(self):
        self.ecrire_chantiers(bloc("alpha", titre="Court", statut="a-venir"),
                              bloc("alpha-2", titre="Long", statut="a-venir"))
        sortie = self.chercher("alpha")
        self.assertEqual(len(re.findall(r"^\S+:\d+ · ", sortie.stdout, flags=re.M)), 1)
        self.assertIn("alpha · a-venir · Court", sortie.stdout)
        self.assertIn("chercher · 1 trouvé(s)", sortie.stdout)

    def test_l_egalite_d_id_respecte_la_casse(self):
        self.ecrire_chantiers(bloc("Alpha", titre="Majuscule", statut="a-venir"),
                              bloc("alpha-2", titre="Minuscule", statut="a-venir"))
        sortie = self.chercher("alpha")
        self.assertIn("chercher · 2 trouvé(s)", sortie.stdout, "pas d'égalité exacte : recherche de sous-chaîne sans casse")
        sortie = self.chercher("Alpha")
        self.assertIn("chercher · 1 trouvé(s)", sortie.stdout)

    def test_partout_cherche_dans_toutes_les_valeurs(self):
        self.assertEqual(self.chercher("module-a").code, 1)
        sortie = self.chercher("module-a", "--partout")
        self.assertEqual(sortie.code, 0)
        self.assertIn("alpha-1 · a-venir · Premier lot", sortie.stdout)
        self.assertIn("chercher · 1 trouvé(s)", sortie.stdout)

    def test_aucun_resultat_donne_le_code_1(self):
        sortie = self.chercher("introuvable")
        self.assertEqual(sortie.code, 1)
        self.assertEqual(sortie.stdout, "chercher · 0 trouvé(s)\n")

    def test_chercher_ne_modifie_rien(self):
        avant = (self.chantiers.read_bytes(), self.archive.read_bytes())
        self.chercher("lot")
        self.chercher("beta-1")
        self.assertEqual((self.chantiers.read_bytes(), self.archive.read_bytes()), avant)


class TestAppelsInvalides(CasArchiver):
    def setUp(self):
        super().setUp()
        self.ecrire_chantiers(bloc("alpha-1", statut="a-venir"))

    def invalide(self, sortie, message: str):
        self.assertEqual(sortie.code, 2, sortie.stdout + sortie.stderr)
        self.assertEqual(sortie.stdout, "")
        self.assertTrue(sortie.stderr.startswith("archiver_chantiers : "), sortie.stderr)
        self.assertIn(message, sortie.stderr)

    def test_sans_commande(self):
        self.invalide(self.lancer(ARCHIVER), "argument manquant")

    def test_commande_inconnue(self):
        sortie = self.lancer(ARCHIVER, "effacer")
        self.invalide(sortie, "commande inconnue : ")
        self.assertRegex(sortie.stderr, r"commande inconnue : '?effacer'? \(archiver ou chercher\)")

    def test_chantiers_manquant(self):
        self.invalide(self.lancer(ARCHIVER, "archiver", "--archives", self.dossier_archives), "argument manquant")

    def test_archives_manquant(self):
        self.invalide(self.lancer(ARCHIVER, "archiver", "--chantiers", self.chantiers), "argument manquant")

    def test_motif_manquant(self):
        self.invalide(self.lancer(ARCHIVER, "chercher", "--chantiers", self.chantiers,
                                  "--archives", self.dossier_archives), "argument manquant")

    def test_argument_inconnu(self):
        self.invalide(self.archiver("--partout"), "argument inconnu : --partout")

    def test_valeur_manquante(self):
        self.invalide(self.lancer(ARCHIVER, "archiver", "--archives", self.dossier_archives, "--chantiers"),
                      "--chantiers : valeur manquante")

    def test_chantiers_absent(self):
        absent = self.dossier / "absent.yaml"
        sortie = self.lancer(ARCHIVER, "archiver", "--chantiers", absent, "--archives", self.dossier_archives)
        self.invalide(sortie, f"fichier introuvable : --chantiers {absent}")

    def test_dossier_d_archives_absent_n_est_jamais_cree(self):
        absent = self.dossier / "nulle-part"
        sortie = self.lancer(ARCHIVER, "archiver", "--chantiers", self.chantiers, "--archives", absent)
        self.invalide(sortie, f"dossier introuvable : --archives {absent}")
        self.assertFalse(absent.exists())

    def test_chercher_chantiers_absent(self):
        absent = self.dossier / "absent.yaml"
        sortie = self.lancer(ARCHIVER, "chercher", "x", "--chantiers", absent, "--archives", self.dossier_archives)
        self.invalide(sortie, f"fichier introuvable : --chantiers {absent}")

    def test_chercher_dossier_d_archives_absent(self):
        absent = self.dossier / "nulle-part"
        sortie = self.lancer(ARCHIVER, "chercher", "x", "--chantiers", self.chantiers, "--archives", absent)
        self.invalide(sortie, f"dossier introuvable : --archives {absent}")

    def test_date_invalide(self):
        for valeur in ("15/03/2026", "2026-02-30", "demain"):
            with self.subTest(valeur=valeur):
                self.invalide(self.archiver(date=valeur), f"--date : AAAA-MM-JJ attendu, reçu « {valeur} »")

    def test_delai_negatif(self):
        self.invalide(self.archiver("--delai", "-1"), "--delai : un nombre de jours positif ou nul est attendu")

    def test_delai_pas_un_entier(self):
        sortie = self.archiver("--delai", "sept")
        self.invalide(sortie, "--delai : un nombre entier est attendu, reçu ")
        self.assertRegex(sortie.stderr, r"reçu '?sept'?")

    def test_fichier_illisible(self):
        self.chantiers = self.ecrire("chantiers.yaml", b"\xff\xfe\x00 pas de l'utf-8", binaire=True)
        sortie = self.archiver()
        self.assertEqual(sortie.code, 2)
        self.assertTrue(sortie.stderr.startswith("archiver_chantiers : "))


class TestFonctions(CasTemporaire):
    @classmethod
    def setUpClass(cls):
        cls.a = charger(ARCHIVER, "archiver_chantiers_sous_test")

    def test_lire_date(self):
        from datetime import date
        self.assertEqual(self.a.lire_date("2026-03-15"), date(2026, 3, 15))
        for valeur in ("", "2026-3-15", "2026-02-30", "15/03/2026", "2026-03-15 ", "abcd-ef-gh"):
            self.assertIsNone(self.a.lire_date(valeur), valeur)

    def test_trouver_blocs(self):
        lignes = ["# t", "", "- id: a", "  statut: dette", "  statut: recette", "", "- id: b", "  titre: x", "texte libre",
                  "  module: perdu"]
        blocs = self.a.trouver_blocs(lignes)
        self.assertEqual([(b.id, b.debut, b.fin) for b in blocs], [("a", 2, 4 + 1), ("b", 6, 8)])
        self.assertEqual(blocs[0].valeur("statut"), "dette", "la première occurrence d'une clé compte")
        self.assertEqual(blocs[1].valeur("module"), "", "une ligne de clé après une ligne hors forme n'est plus du bloc")
        self.assertEqual(blocs[0].ligne, 3)

    def test_resserrer_une_ligne_vide_au_plus_autour_d_un_repere(self):
        self.assertEqual(self.a.resserrer(["a", "", "", None, "", "b"], 0, 0), ["a", "", "b"])
        self.assertEqual(self.a.resserrer(["a", "", None], 0, 0), ["a"])

    def test_en_francais_traduit_les_messages_de_l_analyseur(self):
        self.assertEqual(self.a.en_francais("the following arguments are required: --chantiers"),
                         "argument manquant : --chantiers")
        self.assertEqual(self.a.en_francais("un message inconnu"), "un message inconnu")


if __name__ == "__main__":
    unittest.main()
