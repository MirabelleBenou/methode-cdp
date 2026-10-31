"""Tests de verifier_vivants.py : chacun des dix contrôles, une fois OK et une fois en écart ; les appels invalides.

Chaque test bâtit ses fixtures dans un dossier temporaire (voir outils_tests.py) et appelle le script en
ligne de commande ; quelques tests appellent ses fonctions quand c'est plus net.
"""
import re
import unittest

from .outils_tests import (AVERTISSEMENT, ECART, GENERER, NON_DEMANDE, VERIFIER, CasTemporaire,
                           bloc, charger, registre, yaml)

TABLE_DEUX_DOMAINES = """# Domaines
- domaine: alpha
  cdp: Opus-CdP-Alpha
  checkpoint: CHECKPOINT_ALPHA.md
  file: ## La file
  modules: module-a
  prefixes: alpha-

- domaine: beta
  cdp: Opus-CdP-Beta
  checkpoint: CHECKPOINT_BETA.md
  file: ## La file
  modules: module-b
"""


def checkpoint(*cites: str, historique: tuple = ()) -> str:
    """Un checkpoint : une section de file qui cite les id donnés, puis une section d'historique."""
    file = "".join(f"- `{i}` à faire\n" for i in cites)
    suite = "".join(f"- `{i}` fait\n" for i in historique)
    return f"# Checkpoint\n## État\nRien à signaler.\n## La file\n{file}## Historique\n{suite}"


class CasVerifier(CasTemporaire):
    """Une base qui passe les cinq premiers contrôles ; chaque test en change une pièce."""

    def setUp(self):
        super().setUp()
        self.registre = self.ecrire("registre.md", registre(1, 2, 3))
        self.chantiers = self.ecrire("chantiers.yaml", yaml(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Deuxième", statut="recette", module="module-a", version="v1.0.0")))

    def verifier(self, *options, cwd=None):
        return self.lancer(VERIFIER, "--chantiers", self.chantiers, "--registre", self.registre, *options, cwd=cwd)

    def avec_chantiers(self, *blocs: str, **options):
        """Remplace chantiers.yaml par les blocs donnés."""
        self.chantiers = self.ecrire("chantiers.yaml", yaml(*blocs))

    def archives(self, **fichiers) -> str:
        """Un dossier d'archives ; fichiers : nom (sans extension) -> blocs ; rend le chemin du dossier."""
        dossier = self.sous_dossier("archives")
        for nom, blocs in fichiers.items():
            self.ecrire(f"archives/{nom}.yaml", yaml(*blocs, entete="# Chantiers archivés — Essai"))
        return str(dossier)


class TestAppelDeBase(CasVerifier):
    def test_base_sans_option_aucun_ecart(self):
        sortie = self.verifier()
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(sortie.bilan, "VIVANTS · aucun écart")
        for rang in (1, 2, 3, 4, 5, 8):
            self.assertEqual(sortie.verdict(rang), "OK", f"contrôle {rang}")
        self.assertEqual(sortie.compte(1), "3 numéros, R1 à R3")
        self.assertEqual(sortie.compte(2), "aucune réservation en cours")
        self.assertEqual(sortie.compte(3), "2 chantiers")
        self.assertEqual(sortie.compte(4), "1 versions")
        self.assertEqual(sortie.compte(5), "0 en vol")
        self.assertEqual(sortie.compte(8), "0 livrables, 0 ressources, 0 en vol, 0 en attente")

    def test_non_demande_quand_une_option_manque(self):
        sortie = self.verifier()
        for rang in (6, 7, 9, 10):
            self.assertEqual(sortie.verdict(rang), NON_DEMANDE, f"contrôle {rang}")
        self.assertEqual(len(sortie.controles) - 1, 10, "dix lignes de contrôle, plus le bilan")

    def test_dix_controles_dans_l_ordre(self):
        libelles = re.findall(r"^\d+\s+(\S.*?)\s+(?:OK|ÉCART|avertissement|—)(?:\s|$)", self.verifier().stdout, flags=re.M)
        self.assertEqual(libelles, [
            "numéros du registre", "réservations", "identifiants de chantier", "versions des lots",
            "chantiers en vol", "tableau", "journal", "livrables et ressources", "checkpoints",
            "taille des checkpoints"])

    def test_un_ecart_donne_le_code_1(self):
        self.registre = self.ecrire("registre.md", registre(1, 3))
        sortie = self.verifier()
        self.assertEqual(sortie.code, 1)
        self.assertEqual(sortie.bilan, "VIVANTS · 1 écart(s)")

    def test_un_avertissement_ne_change_pas_le_code(self):
        self.registre = self.ecrire(
            "registre.md", registre(1, 2, 3) + "| **R4** | *réservé par Opus-CdP-Alpha* |\n")
        sortie = self.verifier()
        self.assertEqual(sortie.code, 0)
        self.assertEqual(sortie.bilan, "VIVANTS · aucun écart")

    def test_chemin_du_script_independant_du_dossier_courant(self):
        autre = self.sous_dossier("ailleurs")
        sortie = self.verifier(cwd=autre)
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)


class TestAppelsInvalides(CasVerifier):
    def invalide(self, sortie, message: str):
        self.assertEqual(sortie.code, 2, sortie.stdout + sortie.stderr)
        self.assertEqual(sortie.stdout, "")
        self.assertTrue(sortie.stderr.startswith("verifier_vivants : "), sortie.stderr)
        self.assertIn(message, sortie.stderr)

    def test_sans_aucun_argument(self):
        self.invalide(self.lancer(VERIFIER), "argument manquant : --chantiers")

    def test_option_chantiers_manquante(self):
        self.invalide(self.lancer(VERIFIER, "--registre", self.registre), "argument manquant : --chantiers")

    def test_option_registre_manquante(self):
        self.invalide(self.lancer(VERIFIER, "--chantiers", self.chantiers), "argument manquant : --registre")

    def test_fichier_absent(self):
        absent = self.dossier / "absent.md"
        sortie = self.lancer(VERIFIER, "--chantiers", self.chantiers, "--registre", absent)
        self.invalide(sortie, f"fichier introuvable : --registre {absent}")

    def test_chantiers_absent(self):
        absent = self.dossier / "absent.yaml"
        sortie = self.lancer(VERIFIER, "--chantiers", absent, "--registre", self.registre)
        self.invalide(sortie, f"fichier introuvable : --chantiers {absent}")

    def test_dossier_d_archives_absent(self):
        sortie = self.verifier("--archives", self.dossier / "nulle-part")
        self.invalide(sortie, "fichier introuvable : --archives")

    def test_archives_qui_est_un_fichier(self):
        sortie = self.verifier("--archives", self.registre)
        self.invalide(sortie, "fichier introuvable : --archives")

    def test_domaines_absent(self):
        sortie = self.verifier("--domaines", self.dossier / "absent.yaml")
        self.invalide(sortie, "fichier introuvable : --domaines")

    def test_racine_absente(self):
        table = self.ecrire("domaines.yaml", TABLE_DEUX_DOMAINES)
        sortie = self.verifier("--domaines", table, "--racine", self.dossier / "nulle-part")
        self.invalide(sortie, "fichier introuvable : --racine")

    def test_tableau_sans_generateur(self):
        tableau = self.ecrire("chantiers.html", "<html></html>")
        self.invalide(self.verifier("--tableau", tableau), "--tableau et --generateur vont ensemble")

    def test_generateur_sans_tableau(self):
        self.invalide(self.verifier("--generateur", GENERER), "--tableau et --generateur vont ensemble")

    def test_racine_sans_domaines(self):
        self.invalide(self.verifier("--racine", self.dossier), "--racine ne va qu'avec --domaines")

    def test_plafond_sans_domaines(self):
        self.invalide(self.verifier("--plafond-checkpoint", "100"),
                      "--plafond-checkpoint ne va qu'avec --domaines")

    def test_plafond_zero(self):
        table = self.ecrire("domaines.yaml", TABLE_DEUX_DOMAINES)
        sortie = self.verifier("--domaines", table, "--plafond-checkpoint", "0")
        self.invalide(sortie, "--plafond-checkpoint : un entier positif est attendu (0)")

    def test_plafond_pas_un_entier(self):
        table = self.ecrire("domaines.yaml", TABLE_DEUX_DOMAINES)
        for valeur in ("abc", "-5", "1.5", ""):
            with self.subTest(valeur=valeur):
                sortie = self.verifier("--domaines", table, "--plafond-checkpoint", valeur)
                self.invalide(sortie, "un entier positif est attendu")

    def test_argument_inconnu(self):
        self.invalide(self.verifier("--inconnu", "x"), "argument inconnu : --inconnu")

    def test_valeur_manquante(self):
        sortie = self.lancer(VERIFIER, "--registre", self.registre, "--chantiers")
        self.invalide(sortie, "valeur manquante")

    def test_fichier_illisible_est_un_appel_invalide(self):
        illisible = self.ecrire("registre.md", b"\xff\xfe\x00 pas de l'utf-8", binaire=True)
        sortie = self.lancer(VERIFIER, "--chantiers", self.chantiers, "--registre", illisible)
        self.assertEqual(sortie.code, 2)
        self.assertTrue(sortie.stderr.startswith("verifier_vivants : "))


class TestControle1Numeros(CasVerifier):
    def avec_registre(self, texte: str):
        self.registre = self.ecrire("registre.md", texte)
        return self.verifier()

    def test_ok(self):
        sortie = self.avec_registre(registre(1, 2, 3, 4))
        self.assertEqual(sortie.verdict(1), "OK")
        self.assertEqual(sortie.compte(1), "4 numéros, R1 à R4")
        self.assertEqual(sortie.details(1), [])

    def test_le_plus_petit_numero_n_est_pas_forcement_1(self):
        sortie = self.avec_registre(registre(41, 42, 43))
        self.assertEqual(sortie.verdict(1), "OK")
        self.assertEqual(sortie.compte(1), "3 numéros, R41 à R43")

    def test_ecart_doublon(self):
        sortie = self.avec_registre(registre(1, 2, 2, 3))
        self.assertEqual(sortie.verdict(1), ECART)
        self.assertEqual(sortie.details(1), ["R2 en double (lignes 3, 4)"])
        self.assertEqual(sortie.compte(1), "4 numéros, R1 à R3")
        self.assertEqual(sortie.code, 1)

    def test_ecart_trou_d_un_numero(self):
        sortie = self.avec_registre(registre(1, 3))
        self.assertEqual(sortie.verdict(1), ECART)
        self.assertEqual(sortie.details(1), ["R2 manquant"])

    def test_ecart_trou_de_plusieurs_numeros(self):
        sortie = self.avec_registre(registre(1, 2, 5))
        self.assertEqual(sortie.verdict(1), ECART)
        self.assertEqual(sortie.details(1), ["R3 à R4 (2 numéros) manquants"])
        self.assertEqual(sortie.compte(1), "3 numéros, R1 à R5")

    def test_ecart_plusieurs_trous(self):
        sortie = self.avec_registre(registre(1, 3, 6, 7))
        self.assertEqual(sortie.details(1), ["R2 manquant", "R4 à R5 (2 numéros) manquants"])

    def test_ecart_aucun_numero(self):
        sortie = self.avec_registre("# Registre\nrien ici\n")
        self.assertEqual(sortie.verdict(1), ECART)
        self.assertEqual(sortie.compte(1), "aucun numéro trouvé")
        self.assertEqual(sortie.details(1), ["aucune ligne « | **R<n>** | » dans le registre"])

    def test_les_lignes_qui_ne_sont_pas_des_numeros_sont_ignorées(self):
        sortie = self.avec_registre(registre(1, 2) + "| R3 | pas en gras |\n| **R9 | cassé |\ntexte | **R8** | hors tableau\n")
        self.assertEqual(sortie.verdict(1), "OK")
        self.assertEqual(sortie.compte(1), "2 numéros, R1 à R2")


class TestControle2Reservations(CasVerifier):
    def avec_registre(self, texte: str):
        self.registre = self.ecrire("registre.md", texte)
        return self.verifier()

    def test_ok_aucune_reservation(self):
        sortie = self.verifier()
        self.assertEqual(sortie.verdict(2), "OK")
        self.assertEqual(sortie.compte(2), "aucune réservation en cours")

    def test_avertissement_une_reservation(self):
        sortie = self.avec_registre(registre(1, 2, 3) + "| **R4** | *réservé par Opus-CdP-Alpha* |\n")
        self.assertEqual(sortie.verdict(2), AVERTISSEMENT)
        self.assertEqual(sortie.compte(2), "1 réservation(s) en cours")
        self.assertEqual(sortie.details(2), ["R4 réservé (ligne 5)"])
        self.assertEqual(sortie.verdict(1), "OK", "une réservation est bien un numéro du registre")

    def test_avertissement_plusieurs_reservations(self):
        sortie = self.avec_registre(
            registre(1, 2) + "| **R3** | *réservé par Opus-CdP-Alpha* |\n| **R4** |  *réservé par Opus-CdP-Beta* |\n")
        self.assertEqual(sortie.verdict(2), AVERTISSEMENT)
        self.assertEqual(sortie.compte(2), "2 réservation(s) en cours")
        self.assertEqual(sortie.details(2), ["R3 réservé (ligne 4)", "R4 réservé (ligne 5)"])
        self.assertEqual(sortie.code, 0)

    def test_sans_asterisque_ce_n_est_pas_une_reservation(self):
        sortie = self.avec_registre(registre(1, 2) + "| **R3** | réservé, sans astérisque |\n")
        self.assertEqual(sortie.verdict(2), "OK")


class TestControle3Identifiants(CasVerifier):
    def test_ok(self):
        sortie = self.verifier()
        self.assertEqual((sortie.verdict(3), sortie.compte(3)), ("OK", "2 chantiers"))

    def test_ecart_id_en_double(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir"), bloc("alpha-1", statut="dette"))
        sortie = self.verifier()
        self.assertEqual(sortie.verdict(3), ECART)
        self.assertEqual(sortie.compte(3), "2 chantiers")
        self.assertEqual(len(sortie.details(3)), 1)
        self.assertRegex(sortie.details(3)[0], r"^id alpha-1 en double \(lignes 3, 6\)$")

    def test_les_entrees_sans_id_ne_sont_pas_des_doublons(self):
        self.chantiers = self.ecrire(
            "chantiers.yaml", "# Chantiers — Essai\n\n- titre: Sans id\n  statut: a-venir\n\n- titre: Autre\n  statut: dette\n")
        self.assertEqual(self.verifier().verdict(3), "OK")

    def test_archives_vides_le_compte_les_mentionne(self):
        sortie = self.verifier("--archives", self.archives())
        self.assertEqual((sortie.verdict(3), sortie.compte(3)), ("OK", "2 chantiers, 0 archivés"))

    def test_archives_ok(self):
        dossier = self.archives(**{"CHANTIERS_2026-03": [bloc("beta-1", statut="recette")]})
        sortie = self.verifier("--archives", dossier)
        self.assertEqual((sortie.verdict(3), sortie.compte(3)), ("OK", "2 chantiers, 1 archivés"))

    def test_ecart_id_vivant_aussi_archive(self):
        dossier = self.archives(**{"CHANTIERS_2026-03": [bloc("alpha-1", statut="recette")]})
        sortie = self.verifier("--archives", dossier)
        self.assertEqual(sortie.verdict(3), ECART)
        self.assertEqual(len(sortie.details(3)), 1)
        self.assertTrue(sortie.details(3)[0].startswith("id alpha-1 aussi archivé (CHANTIERS_2026-03.yaml:"),
                        sortie.details(3))

    def test_ecart_id_archive_deux_fois(self):
        dossier = self.archives(**{"CHANTIERS_2026-02": [bloc("beta-1", statut="recette")],
                                   "CHANTIERS_2026-03": [bloc("beta-1", statut="recette")]})
        sortie = self.verifier("--archives", dossier)
        self.assertEqual(sortie.verdict(3), ECART)
        self.assertEqual(sortie.compte(3), "2 chantiers, 2 archivés")
        self.assertRegex(sortie.details(3)[0], r"^id beta-1 en double dans les archives "
                                              r"\(CHANTIERS_2026-02\.yaml:\d+, CHANTIERS_2026-03\.yaml:\d+\)$")

    def test_sans_archives_un_id_archive_reutilise_passe(self):
        self.archives(**{"CHANTIERS_2026-03": [bloc("alpha-1", statut="recette")]})
        self.assertEqual(self.verifier().verdict(3), "OK")

    def test_seuls_les_fichiers_chantiers_yaml_sont_des_archives(self):
        dossier = self.archives(**{"AUTRE": [bloc("alpha-1", statut="recette")]})
        sortie = self.verifier("--archives", dossier)
        self.assertEqual((sortie.verdict(3), sortie.compte(3)), ("OK", "2 chantiers, 0 archivés"))


class TestControle4Versions(CasVerifier):
    def test_ok(self):
        self.avec_chantiers(bloc("alpha-1", statut="recette", version="v1.0.0"),
                            bloc("alpha-2", statut="recette", version="v1.1.0"),
                            bloc("alpha-3", statut="a-venir"))
        sortie = self.verifier()
        self.assertEqual((sortie.verdict(4), sortie.compte(4)), ("OK", "2 versions"))

    def test_ecart_version_portee_deux_fois(self):
        self.avec_chantiers(bloc("alpha-1", statut="recette", version="v1.0.0"),
                            bloc("alpha-2", statut="recette", version="v1.0.0"))
        sortie = self.verifier()
        self.assertEqual(sortie.verdict(4), ECART)
        self.assertEqual(sortie.compte(4), "1 versions")
        self.assertEqual(sortie.details(4), ["version v1.0.0 portée par alpha-1 et alpha-2"])


class TestControle5EnVol(CasVerifier):
    def test_ok_avec_cdp(self):
        self.avec_chantiers(bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha"),
                            bloc("alpha-2", statut="a-venir"))
        sortie = self.verifier()
        self.assertEqual((sortie.verdict(5), sortie.compte(5)), ("OK", "1 en vol"))

    def test_ecart_en_vol_sans_cdp(self):
        self.avec_chantiers(bloc("alpha-1", statut="en-vol"))
        sortie = self.verifier()
        self.assertEqual(sortie.verdict(5), ECART)
        self.assertEqual(sortie.compte(5), "1 en vol")
        self.assertEqual(sortie.details(5), ["alpha-1 (ligne 3) : cdp absent ou vide"])

    def test_ecart_en_vol_avec_cdp_vide(self):
        self.avec_chantiers(bloc("alpha-1", statut="en-vol", cdp=""))
        self.assertEqual(self.verifier().verdict(5), ECART)

    def test_une_entree_sans_id_est_nommee_par_sa_ligne(self):
        self.chantiers = self.ecrire("chantiers.yaml", "# Chantiers — Essai\n\n- titre: Sans id\n  statut: en-vol\n")
        sortie = self.verifier()
        self.assertEqual(sortie.verdict(5), ECART)
        self.assertEqual(sortie.details(5), ["(sans id, ligne 3) (ligne 3) : cdp absent ou vide"])

    def test_les_autres_statuts_n_ont_pas_besoin_de_cdp(self):
        self.avec_chantiers(*(bloc(f"alpha-{n}", statut=s) for n, s in
                              enumerate(("a-venir", "a-cadrer", "dette", "recette"), start=1)))
        sortie = self.verifier()
        self.assertEqual((sortie.verdict(5), sortie.compte(5)), ("OK", "0 en vol"))


class TestControle6Tableau(CasVerifier):
    def setUp(self):
        super().setUp()
        self.tableau = self.dossier / "chantiers.html"
        self.donnees = self.dossier / "chantiers.json"
        self.regenerer()

    def regenerer(self):
        sortie = self.lancer(GENERER, self.chantiers, self.tableau)
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)

    def verifier_tableau(self):
        return self.verifier("--tableau", self.tableau, "--generateur", GENERER)

    def test_ok(self):
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), "OK", sortie.stdout)
        self.assertEqual(sortie.compte(6), f"2 chantiers, page {self.tableau.stat().st_size} octets et données "
                                           f"{self.donnees.stat().st_size} octets identiques hors date")
        self.assertEqual(sortie.code, 0)

    def test_ok_malgre_une_autre_date(self):
        texte = self.donnees.read_text(encoding="utf-8")
        self.assertRegex(texte, r"\d{2}/\d{2}/\d{4}")
        self.donnees.write_text(re.sub(r"\d{2}/\d{2}/\d{4}", "01/01/2000", texte), encoding="utf-8")
        self.assertEqual(self.verifier_tableau().verdict(6), "OK")

    def test_ok_avec_une_page_publiee_sous_un_autre_dossier_et_un_autre_nom(self):
        autre = self.sous_dossier("publie")
        tableau = autre / "tableau.html"
        self.assertEqual(self.lancer(GENERER, self.chantiers, tableau).code, 0)
        sortie = self.verifier("--tableau", tableau, "--generateur", GENERER)
        self.assertEqual(sortie.verdict(6), "OK", sortie.stdout)

    def test_ecart_page_desynchronisee_avec_un_autre_projet(self):
        self.chantiers = self.ecrire("chantiers.yaml", yaml(
            bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"),
            bloc("alpha-2", titre="Deuxième", statut="recette", module="module-a", version="v1.0.0"),
            entete="# Chantiers — Autre projet"))
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(sortie.compte(6), "2 chantiers")
        details = sortie.details(6)
        self.assertEqual(len(details), 2, details)
        self.assertTrue(details[0].startswith("la page du tableau diffère de sa régénération (dates masquées) : "
                                              "premier écart à l'octet "), details)
        self.assertTrue(details[1].startswith("le fichier de données diffère de sa régénération (dates masquées) : "
                                              "premier écart à l'octet "), details)
        self.assertEqual(sortie.code, 1)

    def test_ecart_donnees_desynchronisees_page_intacte(self):
        self.avec_chantiers(bloc("alpha-1", titre="Premier", statut="a-venir"),
                            bloc("alpha-2", titre="Deuxième", statut="recette"),
                            bloc("alpha-3", titre="Ajouté après", statut="dette"))
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(sortie.compte(6), "3 chantiers")
        self.assertEqual(len(sortie.details(6)), 1, "la page est fixe : elle ne diffère pas, seules les données")
        self.assertTrue(sortie.details(6)[0].startswith("le fichier de données diffère de sa régénération "
                                                        "(dates masquées) : premier écart à l'octet "), sortie.details(6))
        self.assertRegex(sortie.details(6)[0], r"\(ligne \d+\) ; \d+ octets contre \d+ régénérés$")
        self.assertEqual(sortie.code, 1)

    def test_ecart_donnees_modifiees_a_la_main_page_intacte(self):
        self.donnees.write_text(self.donnees.read_text(encoding="utf-8").replace("Premier", "Retouché"), encoding="utf-8")
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(len(sortie.details(6)), 1)
        self.assertTrue(sortie.details(6)[0].startswith("le fichier de données diffère"), sortie.details(6))

    def test_ecart_page_modifiee_a_la_main_donnees_intactes(self):
        self.tableau.write_text(self.tableau.read_text(encoding="utf-8") + "<!-- retouche -->\n", encoding="utf-8")
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(len(sortie.details(6)), 1)
        self.assertTrue(sortie.details(6)[0].startswith("la page du tableau diffère"), sortie.details(6))

    def test_ecart_fichier_de_donnees_absent(self):
        self.donnees.unlink()
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(sortie.details(6), [f"fichier de données absent : {self.donnees}"])
        self.assertEqual(sortie.code, 1)

    def test_ecart_donnees_absentes_et_page_retouchee_donnent_deux_lignes(self):
        self.donnees.unlink()
        self.tableau.write_text(self.tableau.read_text(encoding="utf-8") + "<!-- retouche -->\n", encoding="utf-8")
        details = self.verifier_tableau().details(6)
        self.assertEqual(len(details), 2, details)
        self.assertTrue(details[0].startswith("fichier de données absent : "), details)
        self.assertTrue(details[1].startswith("la page du tableau diffère"), details)

    def test_ecart_generateur_qui_echoue(self):
        faux = self.ecrire("faux_generateur.py", "import sys\nsys.exit(3)\n")
        sortie = self.verifier("--tableau", self.tableau, "--generateur", faux)
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(sortie.details(6), ["le générateur a échoué (code 3) : sans message"])

    def test_ecart_generateur_qui_refuse_la_source(self):
        self.avec_chantiers(bloc("alpha-1", statut="statut-inconnu"))
        sortie = self.verifier_tableau()
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertTrue(sortie.details(6)[0].startswith("le générateur a échoué (code 1) : ARRÊT : statut inconnu"),
                        sortie.details(6))

    def test_generateur_qui_ne_produit_rien(self):
        vide = self.ecrire("vide.py", "pass\n")
        sortie = self.verifier("--tableau", self.tableau, "--generateur", vide)
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertTrue(sortie.details(6)[0].startswith("le générateur a échoué (code 0)"), sortie.details(6))

    def test_generateur_qui_n_ecrit_que_la_page(self):
        seul = self.ecrire("page_seule.py", "import sys\nopen(sys.argv[2], 'w').write('<html></html>')\n")
        sortie = self.verifier("--tableau", self.tableau, "--generateur", seul)
        self.assertEqual(sortie.verdict(6), ECART)
        self.assertEqual(sortie.details(6), ["le générateur n'a pas écrit le fichier de données chantiers.json"])


class TestControle7Journal(CasVerifier):
    PLAN = "# Plan\n\n| Version | Contenu |\n|---|---|\n| `v1.0.0` | première |\n| `v1.1.0` | seconde |\n"

    def setUp(self):
        super().setUp()
        self.plan = self.ecrire("plan.md", self.PLAN)

    def verifier_journal(self, *options):
        return self.verifier("--journal", self.plan, *options)

    def test_ok_version_en_recette(self):
        self.avec_chantiers(bloc("alpha-1", statut="recette", version="v1.1.0"))
        sortie = self.verifier_journal()
        self.assertEqual((sortie.verdict(7), sortie.compte(7)), ("OK", "dernière version v1.1.0"))

    def test_ok_quand_l_id_contient_la_version(self):
        self.avec_chantiers(bloc("lot-v1.1.0", statut="recette"))
        self.assertEqual(self.verifier_journal().verdict(7), "OK")

    def test_seule_la_derniere_version_compte(self):
        self.avec_chantiers(bloc("alpha-1", statut="recette", version="v1.0.0"))
        sortie = self.verifier_journal()
        self.assertEqual(sortie.verdict(7), ECART)
        self.assertEqual(sortie.compte(7), "dernière version v1.1.0")

    def test_ecart_aucune_entree_en_recette(self):
        sortie = self.verifier_journal()
        self.assertEqual(sortie.verdict(7), ECART)
        self.assertEqual(sortie.details(7), ["v1.1.0 : aucune entrée en statut recette ne porte cette version"])

    def test_ecart_l_entree_existe_mais_pas_en_recette(self):
        self.avec_chantiers(bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", version="v1.1.0"))
        sortie = self.verifier_journal()
        self.assertEqual(sortie.verdict(7), ECART)
        self.assertEqual(sortie.details(7), [
            "v1.1.0 : aucune entrée en statut recette ne porte cette version",
            "alpha-1 la porte mais est en statut en-vol"])

    def test_ecart_aucune_version_dans_le_journal(self):
        self.plan = self.ecrire("plan.md", "# Plan\n\nrien de versionné\n")
        sortie = self.verifier_journal()
        self.assertEqual(sortie.verdict(7), ECART)
        self.assertEqual(sortie.compte(7), "aucune version")
        self.assertEqual(sortie.details(7), ["aucune ligne « | `v…` | » dans le journal"])

    def test_avec_archives_l_entree_archivee_etait_en_recette(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir"))
        dossier = self.archives(**{"CHANTIERS_2026-03": [bloc("alpha-9", statut="recette", version="v1.1.0")]})
        self.assertEqual(self.verifier_journal().verdict(7), ECART, "sans --archives, l'entrée archivée est invisible")
        self.assertEqual(self.verifier_journal("--archives", dossier).verdict(7), "OK")


class TestControle8Livrables(CasVerifier):
    def controle8(self, *blocs: str):
        self.avec_chantiers(*blocs)
        return self.verifier()

    def test_ok_un_seul_lot_en_vol_par_livrable_et_par_ressource(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", livrable="app-x"),
            bloc("alpha-2", statut="a-venir", livrable="app-x"),
            bloc("alpha-3", statut="en-vol", cdp="Opus-CdP-Beta", ressource="machine-1"))
        self.assertEqual(sortie.verdict(8), "OK")
        self.assertEqual(sortie.compte(8), "1 livrables, 1 ressources, 2 en vol, 0 en attente")

    def test_ecart_deux_lots_en_vol_sur_un_livrable(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", livrable="app-x"),
            bloc("alpha-2", statut="en-vol", cdp="Opus-CdP-Beta", livrable="app-x"))
        self.assertEqual(sortie.verdict(8), ECART)
        self.assertEqual(sortie.details(8), ["livrable app-x : 2 lots en vol (alpha-1, alpha-2)"])
        self.assertEqual(sortie.compte(8), "1 livrables, 0 ressources, 2 en vol, 0 en attente")

    def test_ecart_deux_lots_en_vol_sur_une_ressource(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", ressource="machine-1"),
            bloc("alpha-2", statut="en-vol", cdp="Opus-CdP-Beta", ressource="machine-1"))
        self.assertEqual(sortie.verdict(8), ECART)
        self.assertEqual(sortie.details(8), ["ressource machine-1 : 2 lots en vol (alpha-1, alpha-2)"])

    def test_un_livrable_et_une_ressource_de_meme_nom_ne_se_melangent_pas(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", livrable="commun"),
            bloc("alpha-2", statut="en-vol", cdp="Opus-CdP-Beta", ressource="commun"))
        self.assertEqual(sortie.verdict(8), "OK")
        self.assertEqual(sortie.compte(8), "1 livrables, 1 ressources, 2 en vol, 0 en attente")

    def test_une_entree_qui_porte_les_deux_compte_pour_chacun_et_une_fois_en_vol(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", livrable="app-x", ressource="machine-1"),
            bloc("alpha-2", statut="en-vol", cdp="Opus-CdP-Beta", ressource="machine-1"))
        self.assertEqual(sortie.verdict(8), ECART)
        self.assertEqual(sortie.details(8), ["ressource machine-1 : 2 lots en vol (alpha-1, alpha-2)"])
        self.assertEqual(sortie.compte(8), "1 livrables, 1 ressources, 2 en vol, 0 en attente")

    def test_ecart_attend_un_id_qui_n_existe_pas(self):
        sortie = self.controle8(bloc("alpha-1", statut="a-venir", attend="inconnu"))
        self.assertEqual(sortie.verdict(8), ECART)
        self.assertEqual(sortie.details(8), ["alpha-1 attend inconnu, qui n'existe pas"])
        self.assertEqual(sortie.compte(8), "0 livrables, 0 ressources, 0 en vol, 1 en attente")

    def test_ecart_un_lot_en_vol_qui_attend(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="a-venir"),
            bloc("alpha-2", statut="en-vol", cdp="Opus-CdP-Alpha", attend="alpha-1"))
        self.assertEqual(sortie.verdict(8), ECART)
        self.assertEqual(sortie.details(8), ["alpha-2 est en vol mais attend alpha-1"])

    def test_ok_un_lot_suspendu_qui_attend_un_id_existant(self):
        sortie = self.controle8(
            bloc("alpha-1", statut="en-vol", cdp="Opus-CdP-Alpha", livrable="app-x"),
            bloc("alpha-2", statut="a-venir", livrable="app-x", attend="alpha-1"))
        self.assertEqual(sortie.verdict(8), "OK")
        self.assertEqual(sortie.compte(8), "1 livrables, 0 ressources, 1 en vol, 1 en attente")

    def test_le_controle_8_tourne_sans_autre_option(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", attend="inconnu"))
        sortie = self.lancer(VERIFIER, "--chantiers", self.chantiers, "--registre", self.registre)
        self.assertEqual(sortie.verdict(8), ECART)


class CasCheckpoints(CasVerifier):
    """Deux domaines (alpha, beta), leurs checkpoints et quelques chantiers ; chaque test en change une pièce."""

    def setUp(self):
        super().setUp()
        self.table = self.ecrire("domaines.yaml", TABLE_DEUX_DOMAINES)
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.ecrire("CHECKPOINT_BETA.md", checkpoint("beta-1"))
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))

    def verifier_domaines(self, *options, cwd=None):
        return self.verifier("--domaines", self.table, "--racine", self.dossier, *options, cwd=cwd)


class TestControle9Checkpoints(CasCheckpoints):
    def test_ok(self):
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), "OK", sortie.stdout)
        self.assertEqual(sortie.compte(9), "2 domaines, 0 cités clos, 0 non cités, 0 sans section de file")

    def test_racine_par_defaut_le_dossier_courant(self):
        sortie = self.verifier("--domaines", self.table, cwd=self.dossier)
        self.assertEqual(sortie.verdict(9), "OK", sortie.stdout)
        sortie = self.verifier("--domaines", self.table, cwd=self.sous_dossier("ailleurs"))
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertIn("alpha : checkpoint introuvable CHECKPOINT_ALPHA.md", sortie.details(9))

    def test_ecart_la_file_cite_un_chantier_clos_en_recette(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-0", statut="recette", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-0"))
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["alpha : la file cite alpha-0, clos (recette)"])
        self.assertEqual(sortie.compte(9), "2 domaines, 1 cités clos, 0 non cités, 0 sans section de file")

    def test_ecart_la_file_cite_un_chantier_seulement_archive(self):
        dossier = self.archives(**{"CHANTIERS_2026-03": [bloc("alpha-0", statut="recette")]})
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-0"))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK", "sans --archives, alpha-0 est inconnu")
        sortie = self.verifier_domaines("--archives", dossier)
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["alpha : la file cite alpha-0, clos (archivé)"])

    def test_un_clos_cite_hors_de_la_section_de_file_ne_compte_pas(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-0", statut="recette", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", historique=("alpha-0",)))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_la_section_de_file_s_arrete_au_titre_suivant(self):
        texte = "# Checkpoint\n## La file\n- `alpha-1`\n## Autre\n- `alpha-0` clos, mais plus dans la file\n"
        self.ecrire("CHECKPOINT_ALPHA.md", texte)
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-0", statut="recette", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_le_titre_de_file_est_un_debut_de_ligne(self):
        table = TABLE_DEUX_DOMAINES.replace("file: ## La file\n  modules: module-a", "file: ## §3 · La file\n  modules: module-a")
        self.table = self.ecrire("domaines.yaml", table)
        self.ecrire("CHECKPOINT_ALPHA.md", "# Checkpoint\n## §3 · La file (ce qui vient)\n- `alpha-1`\n")
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_ecart_un_ouvert_non_cite(self):
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint())
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["alpha : alpha-1 (a-venir) n'est pas cité au checkpoint"])
        self.assertEqual(sortie.compte(9), "2 domaines, 0 cités clos, 1 non cités, 0 sans section de file")

    def test_chaque_statut_ouvert_doit_etre_cite_mais_pas_recette(self):
        self.avec_chantiers(*(bloc(f"alpha-{n}", statut=s, module="module-a") for n, s in
                              enumerate(("a-venir", "a-cadrer", "dette", "en-vol", "recette"), start=1)),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint())
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), [
            "alpha : alpha-1 (a-venir) n'est pas cité au checkpoint",
            "alpha : alpha-2 (a-cadrer) n'est pas cité au checkpoint",
            "alpha : alpha-3 (dette) n'est pas cité au checkpoint",
            "alpha : alpha-4 (en-vol) n'est pas cité au checkpoint"])

    def test_un_ouvert_cite_ailleurs_dans_le_checkpoint_est_cite(self):
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint(historique=("alpha-1",)))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_la_citation_se_fait_entre_accents_graves(self):
        self.ecrire("CHECKPOINT_ALPHA.md", "# Checkpoint\n## La file\n- alpha-1 sans accents graves\n")
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["alpha : alpha-1 (a-venir) n'est pas cité au checkpoint"])

    def test_une_entree_avec_pour_n_est_pas_un_sujet(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-msg", statut="a-venir", module="module-a", pour="Opus-CdP-Beta"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_ecart_file_vide_dans_la_table(self):
        table = TABLE_DEUX_DOMAINES.replace("file: ## La file\n  modules: module-a", "file:\n  modules: module-a")
        self.table = self.ecrire("domaines.yaml", table)
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["alpha : aucune section de file déclarée (file: vide)"])
        self.assertEqual(sortie.compte(9), "2 domaines, 0 cités clos, 0 non cités, 1 sans section de file")

    def test_file_vide_la_ligne_precede_les_non_cites_et_9b_ne_s_applique_pas(self):
        table = TABLE_DEUX_DOMAINES.replace("file: ## La file\n  modules: module-a", "file:\n  modules: module-a")
        self.table = self.ecrire("domaines.yaml", table)
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-0", statut="recette", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint(historique=("alpha-0",)))
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), [
            "alpha : aucune section de file déclarée (file: vide)",
            "alpha : alpha-1 (a-venir) n'est pas cité au checkpoint"])

    def test_ecart_checkpoint_introuvable(self):
        (self.dossier / "CHECKPOINT_BETA.md").unlink()
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["beta : checkpoint introuvable CHECKPOINT_BETA.md"])

    def test_ecart_checkpoint_illisible(self):
        self.ecrire("CHECKPOINT_BETA.md", b"\xff\xfe\x00 pas de l'utf-8", binaire=True)
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["beta : checkpoint illisible CHECKPOINT_BETA.md"])

    def test_ecart_section_de_file_introuvable(self):
        self.ecrire("CHECKPOINT_BETA.md", "# Checkpoint\n## Autre chose\n- `beta-1`\n")
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["beta : section de file introuvable « ## La file »"])

    def test_ecart_entree_de_la_table_sans_checkpoint(self):
        table = TABLE_DEUX_DOMAINES + "\n- domaine: gamma\n  cdp: Opus-CdP-Gamma\n"
        self.table = self.ecrire("domaines.yaml", table)
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(9), ECART)
        self.assertEqual(sortie.details(9), ["entrée de la ligne 15 : domaine ou checkpoint manquant"])
        self.assertEqual(sortie.compte(9), "3 domaines, 0 cités clos, 0 non cités, 0 sans section de file")

    def test_ecart_entree_de_la_table_sans_domaine(self):
        table = TABLE_DEUX_DOMAINES + "\n- cdp: Opus-CdP-Gamma\n  checkpoint: CHECKPOINT_GAMMA.md\n"
        self.table = self.ecrire("domaines.yaml", table)
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), ["entrée de la ligne 15 : domaine ou checkpoint manquant"])

    def test_un_domaine_en_defaut_n_est_pas_controle_plus_avant(self):
        self.ecrire("CHECKPOINT_BETA.md", "# Checkpoint\n## Autre chose\n")
        self.avec_chantiers(bloc("beta-1", statut="a-cadrer", module="module-b"),
                            bloc("alpha-1", statut="a-venir", module="module-a"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint())
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), [
            "alpha : alpha-1 (a-venir) n'est pas cité au checkpoint",
            "beta : section de file introuvable « ## La file »"])

    def test_affectation_au_domaine_par_cdp(self):
        self.avec_chantiers(bloc("beta-1", statut="a-cadrer", module="module-b"),
                            bloc("zzz-1", statut="a-venir", cdp="Opus-CdP-Alpha"))
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), ["alpha : zzz-1 (a-venir) n'est pas cité au checkpoint"])

    def test_affectation_au_domaine_par_prefixe(self):
        self.avec_chantiers(bloc("beta-1", statut="a-cadrer", module="module-b"),
                            bloc("alpha-9", statut="a-venir"))
        self.ecrire("CHECKPOINT_ALPHA.md", checkpoint())
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), ["alpha : alpha-9 (a-venir) n'est pas cité au checkpoint"])

    def test_affectation_au_domaine_par_module(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("zzz-1", statut="a-cadrer", module="module-b"))
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), ["beta : zzz-1 (a-cadrer) n'est pas cité au checkpoint"])

    def test_le_cdp_prime_sur_le_prefixe_et_le_module(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("alpha-2", statut="a-venir", module="module-a", cdp="Opus-CdP-Beta"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"))
        self.ecrire("CHECKPOINT_BETA.md", checkpoint("beta-1"))
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.details(9), ["beta : alpha-2 (a-venir) n'est pas cité au checkpoint"])

    def test_une_entree_sans_domaine_n_est_exigee_nulle_part(self):
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", module="module-a"),
                            bloc("beta-1", statut="a-cadrer", module="module-b"),
                            bloc("zzz-1", statut="a-venir", module="module-z"))
        self.assertEqual(self.verifier_domaines().verdict(9), "OK")

    def test_modules_et_prefixes_peuvent_etre_vides(self):
        table = ("- domaine: seul\n  cdp: Opus-CdP-Alpha\n  checkpoint: CHECKPOINT_ALPHA.md\n"
                 "  file: ## La file\n  modules:\n")
        self.table = self.ecrire("domaines.yaml", table)
        self.avec_chantiers(bloc("alpha-1", statut="a-venir", cdp="Opus-CdP-Alpha"))
        sortie = self.verifier_domaines()
        self.assertEqual((sortie.verdict(9), sortie.compte(9)),
                         ("OK", "1 domaines, 0 cités clos, 0 non cités, 0 sans section de file"))

    def test_le_checkpoint_se_lit_depuis_la_racine(self):
        sous = self.sous_dossier("vivants")
        (self.dossier / "CHECKPOINT_ALPHA.md").rename(sous / "CHECKPOINT_ALPHA.md")
        (self.dossier / "CHECKPOINT_BETA.md").rename(sous / "CHECKPOINT_BETA.md")
        sortie = self.verifier("--domaines", self.table, "--racine", sous)
        self.assertEqual(sortie.verdict(9), "OK")


class TestControle10Taille(CasCheckpoints):
    def checkpoint_de(self, octets: int, nom: str = "CHECKPOINT_ALPHA.md"):
        base = checkpoint("alpha-1").encode("utf-8")
        self.assertLess(len(base), octets)
        chemin = self.ecrire(nom, base + b"z" * (octets - len(base)), binaire=True)
        self.assertEqual(chemin.stat().st_size, octets)

    def test_ok(self):
        sortie = self.verifier_domaines()
        self.assertEqual((sortie.verdict(10), sortie.compte(10)), ("OK", "2 domaines, 0 au-delà de 10240 octets"))

    def test_ok_pile_au_plafond_par_defaut(self):
        self.checkpoint_de(10240)
        sortie = self.verifier_domaines()
        self.assertEqual((sortie.verdict(10), sortie.compte(10)), ("OK", "2 domaines, 0 au-delà de 10240 octets"))

    def test_ecart_un_octet_au_dessus_du_plafond_par_defaut(self):
        self.checkpoint_de(10241)
        sortie = self.verifier_domaines()
        self.assertEqual(sortie.verdict(10), ECART)
        self.assertEqual(sortie.compte(10), "2 domaines, 1 au-delà de 10240 octets")
        self.assertEqual(sortie.details(10), ["alpha : CHECKPOINT_ALPHA.md pèse 10241 octets, plafond 10240"])
        self.assertEqual(sortie.code, 1)

    def test_plafond_donne_par_l_option(self):
        self.checkpoint_de(200)
        sortie = self.verifier_domaines("--plafond-checkpoint", "199")
        self.assertEqual(sortie.verdict(10), ECART)
        self.assertEqual(sortie.compte(10), "2 domaines, 1 au-delà de 199 octets")
        self.assertEqual(sortie.details(10), ["alpha : CHECKPOINT_ALPHA.md pèse 200 octets, plafond 199"])
        sortie = self.verifier_domaines("--plafond-checkpoint", "200")
        self.assertEqual(sortie.verdict(10), "OK")

    def test_plafond_de_un_octet_tous_les_checkpoints(self):
        sortie = self.verifier_domaines("--plafond-checkpoint", "1")
        self.assertEqual(sortie.verdict(10), ECART)
        self.assertEqual(len(sortie.details(10)), 2)
        self.assertEqual(sortie.compte(10), "2 domaines, 2 au-delà de 1 octets")

    def test_le_plafond_se_mesure_en_octets_pas_en_caracteres(self):
        # « é » pèse deux octets : 6 caractères, 7 octets
        self.ecrire("CHECKPOINT_ALPHA.md", "abcdé\n" + "## La file\n- `alpha-1`\n")
        taille = (self.dossier / "CHECKPOINT_ALPHA.md").stat().st_size
        sortie = self.verifier_domaines("--plafond-checkpoint", str(taille - 1))
        self.assertEqual(sortie.verdict(10), ECART)

    def test_un_checkpoint_introuvable_est_ignore(self):
        (self.dossier / "CHECKPOINT_BETA.md").unlink()
        sortie = self.verifier_domaines("--plafond-checkpoint", "1")
        self.assertEqual(sortie.verdict(10), ECART)
        self.assertEqual(sortie.details(10), ["alpha : CHECKPOINT_ALPHA.md pèse "
                                              f"{(self.dossier / 'CHECKPOINT_ALPHA.md').stat().st_size} octets, plafond 1"])
        self.assertEqual(sortie.compte(10), "2 domaines, 1 au-delà de 1 octets")

    def test_une_entree_sans_checkpoint_n_est_pas_comptee(self):
        table = TABLE_DEUX_DOMAINES + "\n- domaine: gamma\n  cdp: Opus-CdP-Gamma\n"
        self.table = self.ecrire("domaines.yaml", table)
        sortie = self.verifier_domaines()
        self.assertEqual((sortie.verdict(10), sortie.compte(10)), ("OK", "2 domaines, 0 au-delà de 10240 octets"))

    def test_le_chemin_est_celui_de_la_table(self):
        table = TABLE_DEUX_DOMAINES.replace("checkpoint: CHECKPOINT_ALPHA.md", "checkpoint: sous/CHECKPOINT_ALPHA.md")
        self.table = self.ecrire("domaines.yaml", table)
        self.ecrire("sous/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "z" * 300)
        sortie = self.verifier_domaines("--plafond-checkpoint", "300")
        self.assertEqual(sortie.verdict(10), ECART)
        self.assertTrue(sortie.details(10)[0].startswith("alpha : sous/CHECKPOINT_ALPHA.md pèse "), sortie.details(10))


class TestFonctions(CasTemporaire):
    """Des appels directs aux fonctions du script, quand c'est plus net que la ligne de commande."""

    @classmethod
    def setUpClass(cls):
        cls.v = charger(VERIFIER, "verifier_vivants_sous_test")

    def test_plages(self):
        self.assertEqual(self.v.plages([320, 325, 326, 327]), ["R320", "R325 à R327 (3 numéros)"])
        self.assertEqual(self.v.plages([]), [])
        self.assertEqual(self.v.plages([1, 2]), ["R1 à R2 (2 numéros)"])

    def test_lire_chantiers_garde_la_ligne_et_ignore_commentaires_et_lignes_vides(self):
        chemin = self.ecrire("chantiers.yaml", "# commentaire\n\n- id: a\n  statut: dette\n# autre\n  titre: Un titre: avec deux-points\n")
        entrees = self.v.lire_chantiers(chemin)
        self.assertEqual(len(entrees), 1)
        self.assertEqual(entrees[0]["id"], "a")
        self.assertEqual(entrees[0]["_ligne"], 3)
        self.assertEqual(entrees[0]["_fichier"], "chantiers.yaml")
        self.assertEqual(entrees[0]["titre"], "Un titre: avec deux-points")

    def test_lire_chantiers_ignore_ce_qui_precede_la_premiere_entree(self):
        chemin = self.ecrire("chantiers.yaml", "orphelin: valeur\n- id: a\n")
        self.assertEqual([e["id"] for e in self.v.lire_chantiers(chemin)], ["a"])

    def test_section_de_file(self):
        texte = "# T\n## La file\nun\ndeux\n## Suite\ntrois\n"
        self.assertEqual(self.v.section_de_file(texte, "## La file"), "## La file\nun\ndeux")
        self.assertEqual(self.v.section_de_file(texte, "## Suite"), "## Suite\ntrois\n")
        self.assertIsNone(self.v.section_de_file(texte, "## Absente"))

    def test_domaine_de_premier_qui_convient_regle_apres_regle(self):
        domaines = [{"domaine": "un", "cdp": "X", "modules": "m1", "prefixes": "p-"},
                    {"domaine": "deux", "cdp": "Y", "modules": "m2"}]
        domaine_de = self.v.domaine_de
        self.assertEqual(domaine_de({"id": "p-1", "cdp": "Y", "module": "m1"}, domaines), "deux")
        self.assertEqual(domaine_de({"id": "p-1", "module": "m2"}, domaines), "un")
        self.assertEqual(domaine_de({"id": "q-1", "module": "m2"}, domaines), "deux")
        self.assertIsNone(domaine_de({"id": "q-1", "module": "m3"}, domaines))
        self.assertIsNone(domaine_de({"id": "q-1"}, domaines))

    def test_controle_numeros_sur_un_registre_vide(self):
        chemin = self.ecrire("registre.md", "")
        verdict, compte, _ = self.v.controle_numeros(chemin)
        self.assertEqual((verdict, compte), (ECART, "aucun numéro trouvé"))


if __name__ == "__main__":
    unittest.main()
