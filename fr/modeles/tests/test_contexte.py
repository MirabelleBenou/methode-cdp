"""Tests de contexte.py : la mesure du contexte au dernier tour de la session principale.

Chaque test bâtit, dans un dossier temporaire pris pour « HOME », des journaux synthétiques sous
.claude/projects/<projet>/ (voir outils_tests.py) et lance le script en ligne de commande.
"""
import json
import os
import unittest

from .outils_tests import CONTEXTE, CasTemporaire


def usage(entree=0, lu=0, cree=0, **autres) -> dict:
    """Une ligne de journal : un message avec ses compteurs d'usage ; autres : clés de la ligne (isSidechain…)."""
    return {"type": "assistant", "message": {"role": "assistant", "usage": {
        "input_tokens": entree, "cache_read_input_tokens": lu, "cache_creation_input_tokens": cree,
        "output_tokens": 77}}, **autres}


class CasContexte(CasTemporaire):
    def setUp(self):
        super().setUp()
        self.home = self.sous_dossier("home")
        self.horloge = 1_700_000_000

    def journal(self, chemin: str, *lignes, mtime=None):
        """Un journal sous HOME/.claude/projects/<chemin> ; une ligne est un dict (écrit en JSON) ou un texte brut."""
        fichier = self.home / ".claude" / "projects" / chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text("".join((json.dumps(l) if isinstance(l, dict) else l) + "\n" for l in lignes), encoding="utf-8")
        self.horloge += 10
        os.utime(fichier, (mtime or self.horloge, mtime or self.horloge))
        return fichier

    def contexte(self, *arguments):
        return self.lancer(CONTEXTE, *arguments, env={"HOME": str(self.home), "USERPROFILE": str(self.home)})

    @staticmethod
    def premiere(sortie) -> str:
        """La première ligne de la sortie, sans sa fin de ligne : le contexte au dernier tour."""
        return sortie.stdout.split("\n")[0]

    def assertUneLigne(self, sortie, fragment: str):
        """Échec propre : code 1, une seule ligne, aucune trace d'erreur Python."""
        self.assertEqual(sortie.code, 1, sortie.stdout + sortie.stderr)
        texte = (sortie.stdout + sortie.stderr).strip()
        self.assertEqual(len(texte.split("\n")), 1, texte)
        self.assertNotIn("Traceback", texte)
        self.assertIn(fragment, texte)


class TestMesure(CasContexte):
    def test_mesure_juste_sur_un_cas_simple(self):
        self.journal("p/session.jsonl", usage(10, 200, 30))
        sortie = self.contexte()
        self.assertEqual((sortie.code, self.premiere(sortie), sortie.stderr), (0, "contexte au dernier tour : 240 jetons", ""))

    def test_le_dernier_tour_compte_pas_le_cumul(self):
        self.journal("p/session.jsonl", usage(1, 1000, 100), {"type": "user"}, usage(5, 4000, 300), {"type": "user"})
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 4 305 jetons")

    def test_les_milliers_sont_separes_par_des_espaces(self):
        self.journal("p/session.jsonl", usage(2, 1_234_000, 565))
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 1 234 567 jetons")

    def test_un_compteur_absent_vaut_zero(self):
        self.journal("p/session.jsonl", {"message": {"usage": {"input_tokens": 7, "cache_read_input_tokens": 3}}})
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 10 jetons")

    def test_le_journal_le_plus_recent_est_pris(self):
        self.journal("p/ancien.jsonl", usage(1, 1, 1))
        self.journal("q/recent.jsonl", usage(2, 2, 2))
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 6 jetons")

    def test_un_journal_en_argument_l_emporte(self):
        voulu = self.journal("p/voulu.jsonl", usage(1, 1, 1))
        self.journal("q/plus-recent.jsonl", usage(9, 9, 9))
        self.assertEqual(self.premiere(self.contexte(voulu)), "contexte au dernier tour : 3 jetons")

    def test_un_journal_en_argument_hors_de_home(self):
        autre = self.ecrire("ailleurs/journal.jsonl", json.dumps(usage(4, 5, 6)) + "\n")
        sortie = self.contexte(autre)
        self.assertEqual((sortie.code, self.premiere(sortie)), (0, "contexte au dernier tour : 15 jetons"))


class TestRobustesse(CasContexte):
    def test_aucun_journal(self):
        self.assertUneLigne(self.contexte(), "aucun journal")

    def test_dossier_projects_vide(self):
        (self.home / ".claude" / "projects" / "p").mkdir(parents=True)
        self.assertUneLigne(self.contexte(), "aucun journal")

    def test_journal_sans_ligne_usage(self):
        self.journal("p/session.jsonl", {"type": "user", "message": {"content": "bonjour"}}, {"type": "summary"})
        self.assertUneLigne(self.contexte(), "aucune ligne usage")

    def test_journal_vide(self):
        self.journal("p/session.jsonl")
        self.assertUneLigne(self.contexte(), "aucune ligne usage")

    def test_un_usage_vide_ne_compte_pas(self):
        self.journal("p/session.jsonl", {"message": {"usage": {}}}, {"message": {"usage": None}})
        self.assertUneLigne(self.contexte(), "aucune ligne usage")

    def test_une_ligne_illisible_est_sautee(self):
        self.journal("p/session.jsonl", usage(10, 20, 30), "{ceci n'est pas du json", "", "[1, 2]", "null", usage(1, 2, 3),
                     "{\"tronquée\": ")
        sortie = self.contexte()
        self.assertEqual((sortie.code, self.premiere(sortie)), (0, "contexte au dernier tour : 6 jetons"))

    def test_un_journal_illisible_en_argument(self):
        manquant = self.dossier / "absent.jsonl"
        self.assertUneLigne(self.contexte(manquant), "illisible")
        binaire = self.ecrire("binaire.jsonl", b"\xff\xfe\x00\x01 pas de l'utf-8\n", binaire=True)
        self.assertUneLigne(self.contexte(binaire), "aucune ligne usage")

    def test_un_dossier_en_argument(self):
        self.assertUneLigne(self.contexte(self.sous_dossier("un-dossier")), "illisible")


class TestSessionPrincipale(CasContexte):
    def test_une_ligne_de_sous_agent_plus_recente_est_ignoree(self):
        self.journal("p/session.jsonl", usage(10, 20, 30), usage(900, 900, 900, isSidechain=True))
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 60 jetons")

    def test_une_ligne_isSidechain_false_compte(self):
        self.journal("p/session.jsonl", usage(10, 20, 30), usage(1, 2, 3, isSidechain=False))
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 6 jetons")

    def test_un_journal_fait_seulement_de_lignes_de_sous_agent(self):
        self.journal("p/session.jsonl", usage(1, 2, 3, isSidechain=True))
        self.assertUneLigne(self.contexte(), "aucune ligne usage")

    def test_un_fichier_sous_subagents_est_ecarte(self):
        self.journal("p/principal.jsonl", usage(10, 20, 30))
        self.journal("subagents/agent-1.jsonl", usage(500, 500, 500))
        self.assertEqual(self.premiere(self.contexte()), "contexte au dernier tour : 60 jetons")

    def test_seuls_des_fichiers_sous_subagents(self):
        self.journal("subagents/agent-1.jsonl", usage(500, 500, 500))
        self.assertUneLigne(self.contexte(), "aucun journal")


class TestChargeFixe(CasContexte):
    """Le premier tour est la charge fixe ; le travail est ce qui s'ajoute au dernier tour."""

    def test_trois_tours_et_un_sous_agent_entre_eux(self):
        self.journal("p/session.jsonl", usage(1, 150_000, 82), usage(999_999, isSidechain=True),
                     usage(3, 183_000, 937), usage(0, 254_000, 0))
        sortie = self.contexte()
        self.assertEqual((sortie.code, sortie.stderr), (0, ""))
        self.assertEqual(sortie.stdout, "contexte au dernier tour : 254 000 jetons\n"
                                        "charge fixe (premier tour) : 150 083 jetons\n"
                                        "travail au-dessus de la charge fixe : 103 917 jetons\n")

    def test_les_chiffres_du_cadrage(self):
        self.journal("p/session.jsonl", usage(83, 151_000, 0), usage(999_999, 0, 0, isSidechain=True),
                     usage(940, 183_000, 0), usage(0, 254_000, 0))
        self.assertEqual(self.contexte().stdout, "contexte au dernier tour : 254 000 jetons\n"
                                                 "charge fixe (premier tour) : 151 083 jetons\n"
                                                 "travail au-dessus de la charge fixe : 102 917 jetons\n")

    def test_un_seul_tour_donne_un_travail_de_zero(self):
        self.journal("p/session.jsonl", usage(10, 200, 30))
        self.assertEqual(self.contexte().stdout, "contexte au dernier tour : 240 jetons\n"
                                                 "charge fixe (premier tour) : 240 jetons\n"
                                                 "travail au-dessus de la charge fixe : 0 jetons\n")

    def test_le_premier_tour_ecarte_un_sous_agent_en_tete_et_une_ligne_illisible(self):
        self.journal("p/session.jsonl", usage(900, 900, 900, isSidechain=True), "{illisible", usage(1, 2, 3),
                     usage(4, 5, 6))
        self.assertEqual(self.contexte().stdout, "contexte au dernier tour : 15 jetons\n"
                                                 "charge fixe (premier tour) : 6 jetons\n"
                                                 "travail au-dessus de la charge fixe : 9 jetons\n")

    def test_la_charge_fixe_prend_les_memes_separateurs_de_milliers(self):
        self.journal("p/session.jsonl", usage(2, 1_234_000, 565), usage(0, 2_000_000, 0))
        self.assertEqual(self.contexte().stdout, "contexte au dernier tour : 2 000 000 jetons\n"
                                                 "charge fixe (premier tour) : 1 234 567 jetons\n"
                                                 "travail au-dessus de la charge fixe : 765 433 jetons\n")


class TestCompactage(CasContexte):
    def test_pas_de_marque_pas_de_mention(self):
        self.journal("p/session.jsonl", usage(1, 2, 3))
        self.assertNotIn("compactage", self.contexte().stdout)

    def test_la_marque_isCompactSummary_est_signalee(self):
        self.journal("p/session.jsonl", usage(1, 2, 3), {"type": "user", "isCompactSummary": True}, usage(4, 5, 6))
        sortie = self.contexte()
        self.assertEqual(sortie.code, 0)
        self.assertEqual(sortie.stdout, "contexte au dernier tour : 15 jetons\n"
                                        "charge fixe (premier tour) : 6 jetons\n"
                                        "travail au-dessus de la charge fixe : 9 jetons\n"
                                        "compactage vu : la mesure porte sur le contexte compacté\n")

    def test_la_marque_compact_boundary_est_signalee(self):
        self.journal("p/session.jsonl", {"type": "system", "subtype": "compact_boundary"}, usage(4, 5, 6))
        self.assertEqual(self.contexte().stdout, "contexte au dernier tour : 15 jetons\n"
                                                 "charge fixe (premier tour) : 15 jetons\n"
                                                 "travail au-dessus de la charge fixe : 0 jetons\n"
                                                 "compactage vu : la mesure porte sur le contexte compacté\n")

    def test_une_marque_de_sous_agent_n_est_pas_signalee(self):
        self.journal("p/session.jsonl", usage(4, 5, 6), {"isCompactSummary": True, "isSidechain": True})
        self.assertNotIn("compactage", self.contexte().stdout)

    def test_isCompactSummary_false_n_est_pas_une_marque(self):
        self.journal("p/session.jsonl", usage(4, 5, 6), {"isCompactSummary": False, "subtype": "autre"})
        self.assertNotIn("compactage", self.contexte().stdout)


if __name__ == "__main__":
    unittest.main()
